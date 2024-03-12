import argparse
import csv
import os
import shutil
import sys


def Setup():
    # Set CWD to that of the script
    os.chdir(os.path.dirname(os.path.realpath(__file__))) 

    global mcRecipes
    with open("data/mcRecipes.txt") as mcRecipesFile:
        mcRecipes = mcRecipesFile.read().split('\n')
    

    # Setup Global Variables based from
    global packsMaster
    packsMaster = []
    global craftingPacks
    craftingPacks = []
    global directCopyPacks
    directCopyPacks = []
    global smeltingPacks
    smeltingPacks = []
    global stonecuttingPacks
    stonecuttingPacks = []
    global uncraftingPacks
    uncraftingPacks = []

    with open("data/datapackTypes.csv", 'r') as datapackTypes:
        data = csv.DictReader(datapackTypes)
        for row in data:
            packsMaster.append(row["datapack"])
            match row["type"]:
                case "crafting":
                    craftingPacks.append(row["datapack"])
                case "direct_copy":
                    directCopyPacks.append(row["datapack"])
                case "smelting":
                    smeltingPacks.append(row["datapack"])
                case "stonecutting":
                    stonecuttingPacks.append(row["datapack"])
                case "uncrafting":
                    uncraftingPacks.append(row["datapack"])
                case _:
                    print("Error in datapackTypes.csv")
                    sys.exit(1)

    # Argument Parser Setup
    parser = argparse.ArgumentParser(
        prog = "Generate Datapacks",
        description = "Generates recipes for Stonecutter Extended datapack, and slab uncrafting datapack, and packages them in relevant zip files. \nGenerates the recipes from the '* Data.csv' files in the recipeGen folder",
        epilog = "Created by SirMaxwellSmart (Isaac Beel)"
    )

    parser.add_argument("packs", nargs = '*', choices = packsMaster + ['all'], default = 'all', help = "List all of the packs you wish to generate.")
    parser.add_argument("-ng", "--nogen", action = 'store_true', help = "If present, will not regenerate but only repackage previously generated recipes.")
    parser.add_argument("-na", "--noarchive", action = 'store_true', help = "If present, will not archive the datapacks, but leave them as direcoties in the dataOut folder.")
    parser.add_argument("-p", "--package", nargs = '*', choices = ["c", "combined", "s", "separated"], default = 'combined', help = "Generate a single combined datapack.")
    parser.add_argument("-r", "--release", default = "", help = "Specify an internal version number to prefix datapack name.")
    parser.add_argument("-mc", "--mcversion", default = "1.20", help = "Specify MC version to suffix to name.")
    parser.add_argument("-pf", "--packformat", default = "23", help = "Specify Pack Format for the pack.mcmeta to display.")
    parser.add_argument("-pr", "--packrange", default = "23,34", help = "Specify the Pack Format range (n,n) for the pack.mcmeta to display.")
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

    # Setup vprint for verbose mode
    global vprint
    vprint = print if args.verbose else lambda *a, **k: None
    vprint("NoGen:", args.nogen,"\nNoArchive:", args.noarchive, "\nCombined Output:", combinedOutput, "\nSeparated Ouput:", separatedOutput, "\nRelease No.:", args.release, "\nMC Version:", args.mcversion, "\nPack Format:", args.packformat, "\nPack Range:", args.packrange, "\nVerbose:", args.verbose) # Print options

    global packs
    packs = []
    if 'all' in args.packs:
        packs = packsMaster # Set packs to packMaster if all is selected
    else:
        packs = args.packs # Set packs to arguments provided if all not selected
    vprint("Chosen Packs:", packs)

    main()


def main():
    if args.nogen == False: # Gen Packs
        for datapack in packs:
            shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
            os.makedirs("data/genData/" + datapack, exist_ok=True)

            if datapack in craftingPacks:
                vprint("CraftingGen:", datapack)
                craftingGen(datapack)
            elif datapack in uncraftingPacks:
                vprint("UncraftingGen:", datapack)
                craftingGen(datapack, True)
            elif datapack in stonecuttingPacks:
                vprint("StonecuttingGen:", datapack)
                stonecuttingGen(datapack)
            elif datapack in smeltingPacks:
                vprint("SmeltingGen:", datapack)
                smeltingGen(datapack)

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

    with open("data/templatePack.mcmeta", 'r') as mcmetaTemplateFile:
        global mcmetaTemplate
        mcmetaTemplate = mcmetaTemplateFile.read()

    if args.noarchive == False:
        if separatedOutput:
            for datapack in packs:
                createArchive(datapack)

        if combinedOutput:
            createArchive("extended_combined")


def craftingGen(datapack, uncraft = False):
    shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
    os.makedirs("data/genData/" + datapack, exist_ok=True)

    data = []
    with open("data/packsData/" + datapack + "/data.csv") as dataFile:
        dataRead = csv.DictReader(dataFile)
        for row in dataRead:
            data.append(row)

    with open("data/packsData/" + datapack + "/template.json") as templateFile:
        template = templateFile.read()

    vprint("Template File:")
    vprint(template)
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


def smeltingGen(datapack):
    shutil.rmtree("data/genData/" + datapack, ignore_errors=True)
    os.makedirs("data/genData/" + datapack, exist_ok=True)

    data = []
    with open("data/packsData/" + datapack + "/data.csv") as dataFile:
        dataRead = csv.DictReader(dataFile)
        for row in dataRead:
            data.append(row)

    with open("data/packsData/" + datapack + "/template.json") as templateFile:
        template = templateFile.read()

    vprint("Template File:")
    vprint(template)
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


def stonecuttingGen(datapack):
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


def packTransfer(inDatapack, outDatapack):
    vprint("Transferring:", outDatapack)

    if inDatapack in directCopyPacks:
        shutil.copytree("data/packsData/" + inDatapack, "data/outData/" + outDatapack + "/data/minecraft", dirs_exist_ok = True)

    else:
        datapackRecipes = os.listdir("data/genData/" + inDatapack)
        os.makedirs("data/outData/" + outDatapack + "/data/minecraft/recipes", exist_ok=True)
        os.makedirs("data/outData/" + outDatapack + "/data/" + inDatapack + "/recipes", exist_ok=True)

        for recipe in datapackRecipes:
            if recipe in mcRecipes:
                shutil.copy("data/genData/" + inDatapack + "/" + recipe, "data/outData/" + outDatapack + "/data/minecraft/recipes")
            else:
                shutil.copy("data/genData/" + inDatapack + "/" + recipe, "data/outData/" + outDatapack + "/data/" + inDatapack + "/recipes")


def createArchive(datapack):
    vprint("Creating Archive:", datapack)

    mcmetaTemp = mcmetaTemplate
    mcmetaTemp = mcmetaTemp.replace("PACKFORMAT", args.packformat)
    mcmetaTemp = mcmetaTemp.replace("PACKRANGE", "[" + args.packrange + "]")
    mcmetaTemp = mcmetaTemp.replace("DESCRIPTION", "Combined Packs: " + str(packs) if datapack == "extended_combined" else datapack)

    with open("data/outData/" + datapack + "/pack.mcmeta", 'w') as mcmeta:
        mcmeta.write(mcmetaTemp)
    
    vprint("Creating Archive:", datapack + ".zip")
    outFolder = "Separate Datapacks/" if datapack != "extended_combined" else ""
    releaseOut = '' if args.release == "" else "v" + args.release + " "
    shutil.make_archive(outFolder + releaseOut + datapack + " " + args.mcversion + "+", 'zip', "data/outData/" + datapack)

Setup()
print("---------  Complete!  ---------")