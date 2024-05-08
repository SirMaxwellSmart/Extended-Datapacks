import argparse
import csv
import os
import shutil
import sys
import time


def Setup():
    # Setup master packs and types list
    with open("data/datapackTypes.csv", 'r') as datapackTypesFile:
        datapackTypes = csv.DictReader(datapackTypesFile)
        global master
        master = {}
        for row in datapackTypes:
            master[row["datapack"]] = {"type": row["type"], "overwritemc": row["overwritemc"]}

    # Argument Parser Setup
    parser = argparse.ArgumentParser(
        prog = "Generate Datapacks",
        description = "Generates recipes for Stonecutter Extended datapack, and slab uncrafting datapack, and packages them in relevant zip files. \nGenerates the recipes from the '* Data.csv' files in the recipeGen folder",
        epilog = "Created by SirMaxwellSmart (Isaac Beel)"
    )

    parser.add_argument("packs", nargs = '*', choices = list(master.keys()) + ['all'], default = 'all', help = "List all of the packs you wish to generate.")
    parser.add_argument("-ng", "--nogen", action = 'store_true', help = "If present, will not regenerate but only repackage previously generated recipes.")
    parser.add_argument("-na", "--noarchive", action = 'store_true', help = "If present, will not archive the datapacks, but leave them as direcoties in the dataOut folder.")
    parser.add_argument("-p", "--package", nargs = '*', choices = ["c", "combined", "s", "separated"], default = 'combined', help = "Generate a single combined datapack.")
    parser.add_argument("-r", "--release", default = "", help = "Specify an internal version number to prefix datapack name.")
    parser.add_argument("-mc", "--mcversion", default = "1.21", help = "Specify MC version to suffix to name.")
    parser.add_argument("-pf", "--packformat", default = "41", help = "Specify Pack Format for the pack.mcmeta to display.")
    parser.add_argument("-pr", "--packrange", default = "34,41", help = "Specify the Pack Format range (n,n) for the pack.mcmeta to display.")
    parser.add_argument("-v", "--verbose", action = 'store_true')
    global args
    args = parser.parse_args()

    global combinedOutput
    combinedOutput = False
    global separatedOutput
    separatedOutput = False
    for arg in args.package:
        if arg in ["c", "combined"]:
            combinedOutput = True
        elif arg in ["s", "separated"]:
            separatedOutput = True

    # Setup vprint and timer for verbose mode
    global vprint
    vprint = print if args.verbose else lambda *a, **k: None

    vprint("NoGen:", args.nogen,"\nNoArchive:", args.noarchive, "\nCombined Output:", combinedOutput, "\nSeparated Ouput:", separatedOutput, "\nRelease No.:", args.release, "\nMC Version:", args.mcversion, "\nPack Format:", args.packformat, "\nPack Range:", args.packrange, "\nVerbose:", args.verbose) # Print options

    # Set CWD to that of the script
    vprint("Setting \"Current Working Directory\" to script directory")
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Import mcRecipes.txt
    vprint("Importing mcRecipes.txt")
    global mcRecipes
    with open("data/mcRecipes.txt") as mcRecipesFile:
        mcRecipes = mcRecipesFile.read().split('\n')

    global packs
    packs = []
    if 'all' in args.packs:
        packs = list(master.keys()) # Set packs to packMaster.complete if all is selected
    else:
        packs = args.packs # Set packs to arguments provided if all not selected
    vprint("Chosen Packs:", packs)

    main()


def main():
    if args.nogen == False: # Gen Packs
        timer = time.time()
        vprint("------ Begin Recipe Generation ------")
        for datapack in packs:
            vprint("Clearing Old Data in genData:", datapack)
            shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
            os.makedirs("data/genData/" + datapack, exist_ok=True)

            match master[datapack]["type"]:
                case "crafting":
                    craftingGen(datapack)
                case "direct_copy":
                    pass
                case "smelting":
                    smeltingGen(datapack)
                case "stonecutting":
                    stonecuttingGen(datapack)
                case "uncrafting":
                    craftingGen(datapack, True)
                case _:
                    print("Error in data/datapackTypes.csv")
                    sys.exit(1)

        vprint("Recipe generation completed in", f'{time.time() - timer:.2f}', "s")

    if separatedOutput or combinedOutput: # Begin Datapack Creation
        timer = time.time()
        vprint("------ Begin Datapack Creation ------")

        with open("data/templatePack.mcmeta", 'r') as mcmetaTemplateFile:
            global mcmetaTemplate
            mcmetaTemplate = mcmetaTemplateFile.read()

        if separatedOutput:
            for datapack in packs:
                vprint("Clearing", datapack, "in outData folder")
                shutil.rmtree("data/outData/" + datapack, ignore_errors=True)
                os.makedirs("data/outData/" + datapack, exist_ok=True)
            
                packTransfer(datapack, datapack)

        if combinedOutput:
            vprint("Clearing extended_combined in outData folder")
            shutil.rmtree("data/outData/extended_combined", ignore_errors=True)
            os.makedirs("data/outData/extended_combined", exist_ok=True)
            for datapack in packs:
                packTransfer(datapack, "extended_combined")
        vprint("Transfers completed in:", f'{time.time() - timer:.2f}', "s")

    if args.noarchive == False:
        vprint("------ Begin Archive Creation ------")
        timer = time.time()
        if separatedOutput:
            for datapack in packs:
                createArchive(datapack)

        if combinedOutput:
            createArchive("extended_combined")
        vprint("Archiving completed in:", f'{time.time() - timer:.2f}', "s")


def craftingGen(datapack, uncraft = False):
    timer = time.time()
    vprint("Generating Recipes:", datapack)
    
    shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
    os.makedirs("data/genData/" + datapack, exist_ok=True)

    data = []
    with open("data/packsData/" + datapack + "/data.csv") as dataFile:
        dataRead = csv.DictReader(dataFile)
        for row in dataRead:
            data.append(row)

    with open("data/packsData/" + datapack + "/template.json") as templateFile:
        template = templateFile.read()

    for row in data:

        tempRecipe = template
        tempRecipe = tempRecipe.replace("INPUT", row["input"])
        tempRecipe = tempRecipe.replace("OUTPUT", row["output"])
        tempRecipe = tempRecipe.replace("GROUP", row["group"])
        tempRecipe = tempRecipe.replace("COUNT", row["count"])

        if uncraft:
            recipeName = row["output"] + "_from_" + row["input"]
        else:
            recipeName = row["output"]

        with open("data/genData/" + datapack + "/" + recipeName + ".json", 'w') as recipe:
            recipe.write(tempRecipe)

    vprint("Finished in:", f'{time.time() - timer:.2f}', "s")


def smeltingGen(datapack):
    timer = time.time()
    vprint("Generating Recipes:", datapack)

    shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
    os.makedirs("data/genData/" + datapack, exist_ok=True)

    data = []
    with open("data/packsData/" + datapack + "/data.csv") as dataFile:
        dataRead = csv.DictReader(dataFile)
        for row in dataRead:
            data.append(row)

    with open("data/packsData/" + datapack + "/template.json") as templateFile:
        template = templateFile.read()

    for row in data:
        # Furnace Recipe
        if "f" in row["smeltTypes"]:
            tempRecipe = template
            tempRecipe = tempRecipe.replace("INPUT", row["input"])
            tempRecipe = tempRecipe.replace("OUTPUT", row["output"])
            tempRecipe = tempRecipe.replace("GROUP", row["group"])
            tempRecipe = tempRecipe.replace("TIME", row["time"])
            tempRecipe = tempRecipe.replace("EXP", row["exp"])
            tempRecipe = tempRecipe.replace("TYPE", "smelting")

            with open("data/genData/" + datapack + "/" + row["output"] + "_from_smelting_" + row["input"] + ".json", 'w') as recipe:
                recipe.write(tempRecipe)

        # Blaster Recipe
        if "b" in row["smeltTypes"]:
            tempRecipe = template
            tempRecipe = tempRecipe.replace("INPUT", row["input"])
            tempRecipe = tempRecipe.replace("OUTPUT", row["output"])
            tempRecipe = tempRecipe.replace("GROUP", row["group"])
            tempRecipe = tempRecipe.replace("TIME", str(int(row["time"]) / 2))
            tempRecipe = tempRecipe.replace("EXP", row["exp"])
            tempRecipe = tempRecipe.replace("TYPE", "blasting")

            with open("data/genData/" + datapack + "/" + row["output"] + "_from_blasting_" + row["input"] + ".json", 'w') as recipe:
                recipe.write(tempRecipe)
        
        # Campfire Recipe
        if "c" in row["smeltTypes"]:
            tempRecipe = template
            tempRecipe = tempRecipe.replace("INPUT", row["input"])
            tempRecipe = tempRecipe.replace("OUTPUT", row["output"])
            tempRecipe = tempRecipe.replace("GROUP", row["group"])
            tempRecipe = tempRecipe.replace("TIME", str(int(row["time"]) * 3))
            tempRecipe = tempRecipe.replace("EXP", 0)
            tempRecipe = tempRecipe.replace("TYPE", "campfire_cooking")

            with open("data/genData/" + datapack + "/" + row["output"] + "_from_campfire_cooking_" + row["input"] + ".json", 'w') as recipe:
                recipe.write(tempRecipe)
        
        # Smoker Recipe
        if "s" in row["smeltTypes"]:
            tempRecipe = template
            tempRecipe = tempRecipe.replace("INPUT", row["input"])
            tempRecipe = tempRecipe.replace("OUTPUT", row["output"])
            tempRecipe = tempRecipe.replace("GROUP", row["group"])
            tempRecipe = tempRecipe.replace("TIME", str(int(row["time"]) / 2))
            tempRecipe = tempRecipe.replace("EXP", row["exp"])
            tempRecipe = tempRecipe.replace("TYPE", "smoking")

            with open("data/genData/" + datapack + "/" + row["output"] + "_from_smoking_" + row["input"] + ".json", 'w') as recipe:
                recipe.write(tempRecipe)

    vprint("Finished in:", f'{time.time() - timer:.2f}', "s")


def stonecuttingGen(datapack):
    timer = time.time()
    vprint("Generating Recipes:", datapack)

    shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
    os.makedirs("data/genData/" + datapack, exist_ok=True)

    data = []
    with open("data/packsData/" + datapack + "/data.csv", 'r') as dataFile:
        dataRead = csv.DictReader(dataFile)
        for row in dataRead:
            data.append(row)

    with open("data/packsData/" + datapack + "/template.json") as templateFile:
        template = templateFile.read()

    groups = set()
    for row in data:
        groups.add(row["group"])

    for group in groups:
        tempList = []
        for row in data:
            if row["group"] == group:
                tempList.append(row["id"])

            for input in tempList:
                if "slab" not in input:
                    for output in tempList:
                        fileName = output + "_from_" + input + "_stonecutting"
                        if input != output:
                            if "slab" in output:
                                count = "2"
                            else:
                                count = "1"

                            if fileName not in mcRecipes:
                                tempRecipe = template
                                tempRecipe = tempRecipe.replace('INPUT', input)
                                tempRecipe = tempRecipe.replace('OUTPUT', output)
                                tempRecipe = tempRecipe.replace('COUNT', count)
                                with open("data/genData/" + datapack + "/" + fileName + ".json", 'w') as recipe:
                                    recipe.write(tempRecipe)

    vprint("Finished in:", f'{time.time() - timer:.2f}', "s")


def packTransfer(inDatapack, outDatapack):
    vprint("Transferring:", inDatapack, "->", outDatapack)

    if master[inDatapack] == "direct_copy":
        shutil.copytree("data/packsData/" + inDatapack, "data/outData/" + outDatapack + "/data/minecraft", dirs_exist_ok = True)

    else:
        datapackRecipes = os.listdir("data/genData/" + inDatapack)
        os.makedirs("data/outData/" + outDatapack + "/data/minecraft/recipes", exist_ok = True)
        os.makedirs("data/outData/" + outDatapack + "/data/" + inDatapack + "/recipes", exist_ok = True)

        for recipe in datapackRecipes:
            if recipe in mcRecipes:
                if master[inDatapack]["overwritemc"] == "true":
                    shutil.copy("data/genData/" + inDatapack + "/" + recipe, "data/outData/" + outDatapack + "/data/minecraft/recipes")
                else: pass
            else:
                shutil.copy("data/genData/" + inDatapack + "/" + recipe, "data/outData/" + outDatapack + "/data/" + inDatapack + "/recipes")

    mcmetaTemp = mcmetaTemplate
    mcmetaTemp = mcmetaTemp.replace("PACKFORMAT", args.packformat)
    mcmetaTemp = mcmetaTemp.replace("PACKRANGE", "[" + args.packrange + "]")
    mcmetaTemp = mcmetaTemp.replace("DESCRIPTION", "Combined Packs: " + str(packs) if outDatapack == "extended_combined" else outDatapack)

    with open("data/outData/" + outDatapack + "/pack.mcmeta", 'w') as mcmeta:
        mcmeta.write(mcmetaTemp)


def createArchive(datapack):
    vprint("Creating Archive:", datapack + ".zip")
    
    outFolder = "Separate Datapacks/" if datapack != "extended_combined" else ""
    releaseOut = '' if args.release == "" else "v" + args.release + "_"
    shutil.make_archive(outFolder + releaseOut + datapack + "_" + args.mcversion + "+", 'zip', "data/outData/" + datapack)


globalTimer = time.time()
Setup()
vprint("------ Completed in", f'{time.time() - globalTimer:.2f}', "seconds! ------")
if not args.verbose: print("---------  Complete!  ---------")