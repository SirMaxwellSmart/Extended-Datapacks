import argparse
import csv
import os
import shutil
import sys

# Set CWD to that of the script
os.chdir(os.path.dirname(os.path.realpath(__file__))) 

def Setup():
    global mcRecipes
    with open("data/mcrecipes.txt") as mcRecipesFile:
        mcRecipes = mcRecipesFile.read()
    

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

    parser.add_argument("packs", nargs = '*', choices = packsMaster + ['all'], default = 'all', help = "List all of the packs you wish to generate. Leave blank for all")
    parser.add_argument("-ng", "--nogen", action = 'store_true', help = "If present, will not regenerate but only repackage previously generated recipes")
    parser.add_argument("-nt", "--notransfer", action = 'store_true', help = "If present, will generate recipes in data folders, but not package into datapack")
    parser.add_argument("-s", "--seperate", action = 'store_true', help = "Generate seperate outData instead of generating a single combined pack")
    parser.add_argument("-v", "--verbose", action = 'store_true')
    global args
    args = parser.parse_args()

    # Setup vprint for verbose mode
    global vprint
    vprint = print if args.verbose else lambda *a, **k: None
    vprint("NoGen:", args.nogen,"| NoTransfer:", args.notransfer, "| Seperate:", args.seperate, "| Verbose:", args.verbose) # Print options

    main()

def main():
    packs = []
    if 'all' in args.packs:
        packs = packsMaster # Set packs to packMaster if all is selected
    else:
        packs = args.packs # Set packs to arguments provided if all not selected
        if len(packs) == 1:
            args.seperate = True
    vprint("Chosen Packs:", packs)

    if args.nogen == False: # Gen Packs
        shutil.rmtree("data/genData/", ignore_errors=True)
        os.makedirs("data/genData/", exist_ok=True)

        for datapack in packs:
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

    if args.notransfer == False:
        vprint("Clearing old folders in outData folder")
        shutil.rmtree("data/outData/", ignore_errors=True)
        os.makedirs("data/outData/", exist_ok=True)

        for datapack in packs:
            vprint("Transferring:", datapack)
            packTransfer(datapack)

        with open("data/templatePack.mcmeta", 'r') as mcmetaTemplateFile:
            mcmetaTemplate = mcmetaTemplateFile.read()
        
        vprint("Ensuring Ouput folder Exists")
        os.makedirs("Datapacks Output", exist_ok=True)

        if args.seperate:
            
            for datapack in packs:
                mcmetaTemp = mcmetaTemplate
                mcmetaTemp = mcmetaTemp.replace("DESCRIPTION", str(datapack))

                with open("data/outData/" + datapack + "/pack.mcmeta", 'w') as mcmeta:
                    mcmeta.write(mcmetaTemp)
                
                vprint("Creating Zip:", datapack + ".zip")
                shutil.make_archive("Datapacks Output/" + datapack, 'zip', "data/outData/" + datapack)

        else:
            mcmetaTemp = mcmetaTemplate
            mcmetaTemp = mcmetaTemp.replace("DESCRIPTION", "Combined Packs: " + str(packsMaster))

            with open("data/outData/extended_combined/pack.mcmeta", 'w') as mcmeta:
                mcmeta.write(mcmetaTemp)

            vprint("Creating Zip: extended_combined.zip")
            shutil.make_archive("Datapacks Output/extended_combined", 'zip', "data/outData/extended_combined")


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
    for i in data:
        groups.add(i["group"])

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

def packTransfer(namespace):
    if args.seperate:
        datapack = namespace
    else:
        datapack = "extended_combined"

    if namespace in directCopyPacks:
        shutil.copytree("data/packsData/" + namespace, "data/outData/" + datapack + "/data/minecraft", dirs_exist_ok = True)

    else:
        datapackRecipes = os.listdir("data/genData/" + namespace)
        os.makedirs("data/outData/" + datapack + "/data/minecraft/recipes", exist_ok=True)
        os.makedirs("data/outData/" + datapack + "/data/" + namespace + "/recipes", exist_ok=True)

        for recipe in datapackRecipes:
            # vprint("Namespace:", namespace, "Datapack:", datapack, "Recipe:", recipe)

            if recipe in mcRecipes:
                shutil.copy("data/genData/" + namespace + "/" + recipe, "data/outData/" + datapack + "/data/minecraft/recipes")
            else:
                shutil.copy("data/genData/" + namespace + "/" + recipe, "data/outData/" + datapack + "/data/" + namespace + "/recipes")

Setup()
print("---------  Complete!  ---------")