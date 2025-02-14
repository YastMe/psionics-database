import json
import os

import requests
from bs4 import BeautifulSoup


def dedupe():
	print("Deleting duplicates...")
	with open("powers_per_class.json", "r", encoding="utf-8") as f:
		d = json.load(f)
		powers = []
		for class_data in d.items():
			for power in class_data[1]:
				powers.append(power)

		seen = set()
		sorted_and_deduped = []
		for item in sorted(powers, key=lambda x: x['name']):
			if item['name'] not in seen:
				seen.add(item['name'])
				sorted_and_deduped.append(item)
		new_data = {
			"powers": sorted_and_deduped,
			"powers_per_class": d
		}

	with open("powers_per_class.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(new_data, indent=4))


def list_all():
	print("Listing all powers...")
	url = "https://libraryofmetzofitz.fandom.com/wiki/Powers"
	response = requests.get(url)
	soup = BeautifulSoup(response.text, "html.parser")

	links = soup.find_all("a")
	classes = []
	for link in links:
		if "Powers" in link.contents[0]:
			classes.append(link.get("href"))

	base_url = "https://libraryofmetzofitz.fandom.com"
	powers_per_class = {}
	for c in classes:
		url = base_url + c
		class_name = c.split("/")[-1].split("_")[0]
		if class_name == "Wilder":
			class_name = "Psion/Wilder"
		elif class_name == "Psion":
			class_name = "Psion Discipline"
		response = requests.get(url)
		soup = BeautifulSoup(response.text, "html.parser")
		main_page = soup.find("main", {"class": "page__main"})
		if main_page:
			links = main_page.find_all("a")
			for link in links:
				if link.parent.name != "b":
					continue
				else:
					if class_name not in powers_per_class:
						powers_per_class[class_name] = []
					powers_per_class[class_name].append({"name": link.contents[0], "href": base_url + link.get("href")})

	with open("powers_per_class.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(powers_per_class, indent=4))


def get_power_levels():
	with open("powers_per_class.json", "r", encoding="utf-8") as f:
		d = json.load(f)
		powers = d["powers"]
		for power in powers:
			print(f"Working on {power['name']}...")
			response = requests.get(power["href"])
			soup = BeautifulSoup(response.text, "html.parser")
			ps = soup.find_all("p")
			for p in ps:
				if "Level:" in p.text and not "level" in power:
					power["level"] = p.text.split("Level:")[-1].strip().split(",")
				elif "Level" in p.text and not "level" in power:
					power["level"] = p.text.split("Level")[-1].strip().split(",")
				if "Discipline" in p.text:
					if "Discipline:" in p.text:
						power["discipline"] = p.text.split("Discipline:")[-1].strip()
					else:
						power["discipline"] = p.text.split("Discipline")[-1].strip()
					if ";" in power["discipline"]:
						power["discipline"] = power["discipline"].split(";")[0]
				if power == "Oak Body":
					power["level"][0] = "Highlord 5"

		new_powers = {}
		for power in powers:
			new_powers[power["name"]] = {
				"level": power["level"],
				"discipline": power["discipline"],
				"href": power["href"]
			}

		new_data = {
			"powers": new_powers,
			"powers_per_class": d["powers_per_class"]
		}

	with open("powers_per_class.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(new_data, indent=4))


def sort_powers():
	with open("powers_per_class.json", "r", encoding="utf-8") as f:
		d = json.load(f)
		powers = d["powers"]
		disciplines = {}
		for name, power in powers.items():
			discipline = power["discipline"].split(" ")[0].capitalize()
			if "," in discipline:
				discipline = discipline.split(",")[0]
			if discipline == "Athanatism ":
				discipline = "Athanatism"
			elif discipline == "Telekinesis":
				discipline = "Psychokinesis"
			elif discipline == "Psychokinetic":
				discipline = "Psychokinesis"
			if discipline not in disciplines:
				disciplines[discipline] = []
			disciplines[discipline].append({"name": name, "href": power["href"]})

	new_data = {
		"powers": powers,
		"powers_per_class": d["powers_per_class"],
		"disciplines": disciplines
	}
	with open("powers_per_class_and_discipline.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(new_data, indent=4))


def sort_disciplines():
	with open("powers_per_class_and_discipline_sorted.json", "r", encoding="utf-8") as f:
		d = json.load(f)
		disciplines = d["disciplines"]
		discipline_keys = list(disciplines.keys())
		discipline_keys.sort()

		sorted_disciplines = {i: disciplines[i] for i in discipline_keys}
		new_data = {
			"powers": d["powers"],
			"powers_per_class": d["powers_per_class"],
			"disciplines": sorted_disciplines
		}

	with open("powers_per_class_and_discipline_sorted.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(new_data, indent=4))


def fix_levels():
	with open("powers_per_class_and_discipline.json", "r", encoding="utf-8") as f:
		d = json.load(f)
		powers = d["powers"]
		for power_name, power in powers.items():
			print(f"Fixing {power_name}...")
			power["level_dict"] = {}
			for level in power["level"]:
				level = level.replace("\xa0", " ")
				if "Discipline" in level:
					level = "".join(level.split(";")[1]).split("Level")[-1]
				if "psion/wilder1" in level:
					level = " psion/wilder 1"
				if "psion/wilder2" in level:
					level = " psion/wilder 2"
				level = level.strip().title()
				class_name = " ".join(level.split(" ")[:-1])
				try:
					power_level = int(level.split(" ")[-1])
				except ValueError:
					class_name = "Highlord"
					power_level = 5
				power["level_dict"][class_name] = power_level
			powers[power_name] = {
				"discipline": power["discipline"],
				"level": power["level_dict"],
				"href": power["href"]
			}
		new_data = {
			"powers": powers,
			"powers_per_class": d["powers_per_class"],
			"disciplines": d["disciplines"]
		}

	with open("powers_per_class_and_discipline_sorted.json", "w", encoding="utf-8") as f:
		f.write(json.dumps(new_data, indent=4))


if __name__ == "__main__":
	if not os.path.exists("powers_per_class.json"):
		list_all()
		dedupe()
		get_power_levels()
	if not os.path.exists("powers_per_class_and_discipline.json"):
		sort_powers()
	if not os.path.exists("powers_per_class_and_discipline_sorted.json"):
		fix_levels()
		sort_disciplines()
