import csv
import datetime
import os
import re
import argparse
import shutil

NOM_SAL = "NOM_SAL"
NOM_TD = "NOM_DIP"
NOM_ENS = "NOM_ENS"
DDEBUT = "DDEBUT"
HDEBUT = "HDEBUT"
HFIN = "HFIN"
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

def parseSalle(salle):
            
    resalle = re.compile(r"([a-zA-Z0-9]+ [^-<>]+- [^ \(]+)")
    g = resalle.finditer(salle)
    ns = ""
    for m in g:
        ns = ns + (", " if ns != "" else "") + m[1]
    if ns != "":
        return ns
    return salle


def parseFile(in_path, out_path, label):
        
        labels = []
        data = []
        classes = []
        with open(in_path) as inCsv:
            csvreader = csv.DictReader(inCsv, delimiter='\t')# lecture du fichier
            i = True
            for row in csvreader:# chaque ligne
                if i:
                    labels = list(row.keys())# recup des labels
                    i = False
                data.append(row)

        # Creation du tableau pour rassembler les cours d'une meme matiere
        mat = {}
        for row in data:
            grp_nom = row[NOM_TD][-9:]
            if not grp_nom in mat:
                mat[grp_nom] = {
                    "ENSEIGNANT": row[NOM_ENS],
                    "COURS": []
                }

            salle = parseSalle(row[NOM_SAL])

            mat[grp_nom]["COURS"].append({
                "DATE": DAYS[datetime.datetime.strptime((row[DDEBUT]), "%d/%m/%Y").weekday()] + " " + row[DDEBUT][0:5],
                "WEEK": datetime.datetime.strptime((row[DDEBUT]), "%d/%m/%Y").isocalendar()[1],
                "HEURE": row[HDEBUT] + " - " + row[HFIN],
                "SALLE": salle
            })
        # utilité de tri
        def sort_week(elem):
            return elem["WEEK"]

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
        # tri
        for td, dat in mat.items():
            dat["COURS"].sort(key=sort_week)

        out_data = [[label, ""]]

        # on tri les tds
        for td in sorted(mat.keys()):
            out_data.append([td + "\n" + mat[td]["ENSEIGNANT"], "Jour"])
            out_data.append(["", "Horaire"])
            out_data.append(["", "Salle"])
            out_data.append(["", "Assistant"])

        done = False
        while not done:
            done = True
            nextWeek = 100
            for td in sorted(mat.keys()):
                if len(mat[td]["COURS"]) > 0:
                    done = False
                    if mat[td]["COURS"][0]["WEEK"] < nextWeek:
                        nextWeek = mat[td]["COURS"][0]["WEEK"]

            # quelque chose a ajouter?
            if not done:
                out_data[0].append("Semaine " + str(nextWeek))
                i = 0
                for td in sorted(mat.keys()):
                    if len(mat[td]["COURS"]) > 0 and mat[td]["COURS"][0]["WEEK"] == nextWeek:
                        out_data[4*i + 1].append(mat[td]["COURS"][0]["DATE"])
                        out_data[4*i + 2].append(mat[td]["COURS"][0]["HEURE"])
                        out_data[4*i + 3].append(mat[td]["COURS"][0]["SALLE"])
                        out_data[4*i + 4].append("")
                        mat[td]["COURS"].pop(0)
                    else:
                        out_data[4*i + 1].append("")
                        out_data[4*i + 2].append("")
                        out_data[4*i + 3].append("")
                        out_data[4*i + 4].append("")
                    i += 1
        
        # on ecrit le resultat final
        with open(out_path, "w", newline='') as export:
            writer = csv.writer(export, delimiter=';')
            writer.writerows(out_data)
                


parser = argparse.ArgumentParser(description="Ce script sert a générer les fichiers csv permettant le suivi des assistants")
parser.add_argument("-c", "--clean", dest="clean", action="store_true", help="Vide le répértoire de sortie avant de générer les fichiers")
parser.add_argument("-p", "--planning", dest="planning", action="store", default="planning", help="Dossier contenant les csv des cours (par défaut, planning)")
parser.add_argument("-o", "--output", dest="output", action="store", default="out", help="Dossier de sortie (par défaut, out)")
parser.add_argument("-s", "--separator", dest="separator", action="store", default="\t", help="Séparateur dans les fichiers csv (par défaut, \t)")

args = parser.parse_args()

out_folder = "out"

if args.clean:
    for filename in os.listdir(out_folder):
        file_path = os.path.join(out_folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
for filename in os.listdir(args.planning):
    f = os.path.join(args.planning, filename)
    # checking if it is a file
    if os.path.isfile(f) and f.endswith(".csv"):
        parseFile(f, os.path.join(args.output, filename), ".".join(filename.split(".")[:-1]))
                