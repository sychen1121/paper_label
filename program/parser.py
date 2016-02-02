import bibtexparser
import os 
import json
import random
import re
import codecs
import math
# marketing science
fields = ['ID', 'author', 'title', 'journal', 'year', 'volumn', 'number', 'pages', 'month', \
'volume', 'abstract', 'type', 'keyword', 'keywords-plus', 'web-of-science-categories']
input_path = '../input/'
paper_path = "paper/"
topic_path = "topic/"
output_path = '../output/'
public_path = "../website/public/"
parsed_file = "parsed.json"

'''
Data preprocess
'''
'''
Paper
'''
# Description:
# Input:
# Output:
# Return:
def preprocess_paper():
	cate_papers = dict()
	for path, folders, filenames in os.walk(input_path+paper_path):
		papers = list()
		category = str()
		journal = str()
		for filename in filenames:
			if '.bib' in filename:
				category = path.split("/")[-2]
				journal = path.split("/")[-1]
				papers += parse_paper(os.path.join(path, filename))
		if len(papers) > 0: 
			if cate_papers.get(category, 0) == 0:
				cate_papers[category] = dict()
			cate_papers[category][journal] = papers
	write_json(output_path+parsed_file, cate_papers)

def parse_paper(input_file="../input/Marketing/Marketing Science/Marketing Science(1).bib"):
	papers_all = list()
	papers_add = parse_paper_add()
	with open(input_file, "r") as fi:
		papers = bibtexparser.loads(fi.read())
	# one bib one article
	for paper in papers.entries:
		if paper["type"] != "Article":
			continue
		if paper.get("abstract","") == "":
			title = remove_reduct_symbol(paper["title"])
			if papers_add.get(title,"") != "":
				paper["abstract"] = papers_add[title]
			else:
				continue
		paper_info = dict()
		for key, value in paper.items():
			if key in fields:
				paper_info[key] = remove_reduct_symbol(value)
		papers_all.append(paper_info)
	return papers_all

def parse_paper_add():
	papers_abstract = dict()
	with open(input_path+"paper_add", "r") as fi:
		for line in fi:
			tmp = line.split("\t")
			title = tmp[0].strip()
			abstract = tmp[1].strip()
			papers_abstract[title] = abstract
	return papers_abstract



def remove_reduct_symbol(sentence):
	return sentence.replace("\\","").replace("``", "").replace("{''}","").replace("\n", " ").replace("{[}", "[").replace("`","'")

'''
Topic
'''
def preprocess_topic():
	parse_topic_im()
	parse_topic_transportation()
	parse_topic_om()
	parse_topic_marketing()


def parse_topic_im():
	text_origin = str()
	result = list()
	with open(input_path+topic_path+"im", "r") as fi:
		text_origin = fi.read()
	categories = text_origin.split("\n\n")
	for category in categories:
		texts = category.split("\n")
		cate_title = texts[0]
		cate_topic = [{"title": title} for title in texts[1:]]
		result.append({"title": cate_title, "topics": cate_topic})
	result.append(parse_relevant("im"))
	write_json(output_path+"topic_im.json", result)


def parse_topic_transportation():
	text_origin = str()
	result = list()
	with open(input_path+topic_path+"transportation", "r") as fi:
		text_origin = fi.read()
	categories = text_origin.split("\n\n")
	for category in categories:
		texts = category.split("\n")
		cate_title = texts[0].split("	")[1].split("(")[0]
		cate_topic = list()
		for i in range(1, len(texts), 2):
			titles, subs = get_multiple_brackets(texts[i].strip().split("	")[1], "、")
			desc = texts[i+1].strip()
			cate_topic.append({"title": ";".join(titles), "sub": ";".join(subs), "desc": desc})
		result.append({"title": cate_title, "topics": cate_topic})
	result.append(parse_relevant("transportation"))
	# print(json.dumps(result, indent=4))
	write_json(output_path+"topic_transportation.json", result)

def parse_topic_marketing():
	text_origin = str()
	result = list()
	with open(input_path+topic_path+"marketing", "r") as fi:
		text_origin = fi.read()
	categories = text_origin.split("\n\n")
	for category in categories:
		texts = category.split("\n")
		cate_title, cate_sub = get_brackets(texts[0].strip())
		cate_title = cate_title.replace("\t", "")
		cate_desc = texts[1].strip()
		cate_topic = list()
		for text in texts[2:]:
			cate_topic.append({"title": text.strip().replace("\t","")})
		result.append({"title": cate_title, "sub": cate_sub, "desc": cate_desc, "topics": cate_topic})
	result.append(parse_relevant("marketing"))
	write_json(output_path+"topic_marketing.json", result)

def parse_topic_om():
	text_origin = str()
	result = list()
	with open(input_path+topic_path+"om", "r") as fi:
		text_origin = fi.read()
	categories = text_origin.split("\n\n")
	for category in categories:
		texts = category.split("\n")
		cate_title = texts[0]
		cate_topic = list()
		for text in texts[1:]:
			title, sub = get_brackets(text)
			cate_topic.append({"title": title, "sub": sub})
		result.append({"title": cate_title, "topics": cate_topic})
	result.append(parse_relevant("OM&OR"))
	write_json(output_path+"topic_om.json", result)

def parse_relevant(cate):
	result = {"title": "Not Relevant", "topics":["Relevant to IM", "Relevant to Transportation", "Relevant to OM&OR", "Relevant to Marketing"]}
	for topic in result["topics"]:
		if cate.lower() in topic.lower():
			result["topics"].remove(topic)
	return result


'''
DB preprocess
'''


def build_db_data():
	# build_db_user()
	build_db_paper()

# revise the user account and pwd
def build_db_user():
	# data = read_parsed_data()
	data = dict()
	instances = list()
	with open(input_path+"user", "r") as fi:
		cates = fi.read().split("\n\n")
	for cate in cates:
		texts = cate.split("\n")
		title = texts[0].strip()
		for i in range(2):
			name = texts[1+i*2].strip()
			account = texts[2+i*2].strip()
			pwd = create_pwd(4)
			instance = dict()
			instance["account"] = account
			instance["pwd"] = pwd
			instance["name"] = name
			instance["category"] = title
			instance["index"] = str(i+1)
			instances.append(instance)
	build_db_format("user.user", instances, public_path+"data_user.json")

def build_db_paper(threshold=200, ratio=0.1):
	data = read_parsed_data()
	cate_papers = dict()
	instances = list()
	for category, cate_dict in sorted(data.items()):
		# concate papers by sorting journal 
		for journal, papers in sorted(cate_dict.items()):
			for paper in papers:
				paper["category"] = category.lower()
				paper["web_of_science_categories"] = paper.get("web-of-science-categories", "")
				paper.pop("web-of-science-categories")
				paper["isi"] = paper.get("ID", "")
				paper.pop("ID")
				paper["keywords_plus"] = paper.get("keywords-plus", "")
				# paper["label1"] = ""
				# paper["label2"] = ""
				# paper["prediction"] = ""
				if paper["keywords_plus"] != "":
					paper.pop("keywords-plus")
			cate_papers[category] = cate_papers.get(category, list())+papers
	for category, papers in sorted(cate_papers.items()):
		number = max(threshold, int(len(papers)*0.1))
		print(number)
		samples = get_samples(number, len(papers))
		# samples = random.sample(range(len(papers)), number)
		for index, sample in enumerate(samples):
			if index%2 == 0:
				papers[sample]["is_phased1"] = True	
			else:
				papers[sample]["is_phased2"] = True
		instances += papers
	build_db_format("paper.paper", instances, public_path+"data_paper.json")

def build_db_format(model, instances, path):
	rows = list()
	for index, instance in enumerate(instances):
		row = dict()
		row["fields"] = instance
		row["model"] = model
		row["pk"] = index+1
		rows.append(row)
	write_json(path, rows)



''' 
IO
'''

def read_json(path):
	data = dict()
	with open(path, "r") as fi:
		data = json.loads(fi.read())
	return data

def write_json(path, data):
	with codecs.open(path, "w", encoding="utf8") as fo:
		fo.write(json.dumps(data, indent=4, ensure_ascii=False))

def read_parsed_data():
	data = read_json(output_path+parsed_file)
	return data



'''
Others
'''

def get_multiple_brackets(text, mark):
	items = text.split(mark)
	titles = list()
	subs = list()
	for item in items:
		title, sub = get_brackets(item)
		titles.append(title)
		subs.append(sub)
	return titles, subs


def get_brackets(text):
	result = re.search(r'(.+)\((.+)\)', text)
	if result == None:
		return text, ""
	else:
		return result.group(1).strip(), result.group(2).strip()

def get_samples(k, total):
	a = total/k
	b = random.random() * a
	numbers = list()
	for i in range(k):
		numbers.append(math.floor(a*i+b))
	return numbers

def create_pwd(length):
	alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	pwd = ""
	for i in range(length):
		index = random.randrange(len(alphabet))
		pwd= pwd + alphabet[index]
	return pwd


# def save(output_path, articles ):
# 	for article in articles:
# 		with open(os.path.join, "w") as fo:
# 			fo.write(json.dumps(article, indent=4))

if __name__ == "__main__":
	preprocess_paper()
	# preprocess_topic()
	# preprocess_topic()
	
	build_db_data()

