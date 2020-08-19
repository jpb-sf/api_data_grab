from apiclient.discovery import build
import os
import time
import re
import random
import datetime
import csv
from flask import Flask, request, session, url_for, flash, redirect, render_template, json, jsonify, send_from_directory, send_file
import json
import config
import datetime
import requests

#=============================================================================

# # Initiate app
app = Flask(__name__)
app.config.from_object('config.Config')

# .env file
api_key = config.Config.API_KEY

# google api
youtube = build('youtube', 'v3', developerKey=api_key)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expi,methods=['GET'res"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Start App
@app.route('/', methods=['GET'])
def home():
    return render_template('ytdata.html')

# Send message to user on client side if scripting is turned off
@app.route('/error.html')
def error():
    return render_template('/disabled.html')

# Clear user created csv file when user clicks from display back to search or home.
@app.route('/clear/<file>', methods=['GET'])
def clear(file):
	print('file to clear is ' + file)
	try:
		f = open('csv/' + file, 'w')
		os.remove(f.name)
		return 'True'
	except Exception as e:
		print('error removing file')
		return 'False'

# Function returns the age of a file measured in hours (whole integers)
def get_file_age(filepath):
	return int(((time.time() - os.path.getmtime('csv/' + filepath)) / 60) / 60)

# Loops through server's csv directory, and deletes any user-createed csv files older than 2 hours
def clear_old_files():
	for f in os.listdir('csv/'):
		if get_file_age(f) > 2:
			open_f = open('csv/' + f, 'w')
			os.remove(open_f.name)

# Support function that makes additional API call for data of (viewCount, likeCount, commentCount)
def get_stats(videoId):
	try:
		# Call Youtube Api
		stats = youtube.videos().list(id=videoId, part="statistics").execute()
		# Put results into string
		results = {
		'viewCount': stats['items'][0]['statistics']['viewCount'], 
		'likeCount': stats['items'][0]['statistics']['likeCount'],
		'commentCount': stats['items'][0]['statistics']['commentCount'],
		}
		return results
	except Exception as e:
		print(e)
		return 1

# Support function for 'write_CSV()' that updates the global variable, 'html_output'	
def write_HTML(final, *args):
	
	args = list(*args)
	global first, html_output

	column_titles = ["#", "Video Title", "Channel", "Video ID", "Published on", "Views", "Likes", "Comments"] 

	# final call adds closing tags to HTML string, (writes html buttons)
	if final == True:
		html_output += "</table>\n" \
		 + "<button type=\"button\" onclick=\"home()\" class=\"button mt-1\">Search</button>\n" \
		 + "<button type=\"button\" onclick=\"download()\"class=\"button mt-1\">Download</button>\n" 
		return
	
	# If first call of function, write the header text, and header row
	if first:
		html_output += "<h4><i>Query:\"" +  args[0]['query'] + "\" | On: " + args[0]['date'] +" PST</i></h4>\n"  \
		+ "<table class=\"table\">\n" \
		+ "<tr class=\"head\">\n" 
		
		# Loop through column titles and add
		for i in column_titles:
			html_output += "\t<th class=\"cell\">" + i + "</th>\n"
		html_output += "</tr>\n" 
	
	first = False

	html_output += "<tr class=\"row\">\n" 
	
	# add table data cells to row of html string
	for item in args[1]:
		html_output += "\t<td class=\"cell\">" + str(item) + "</td>\n"
	html_output += "</tr>\n"


# writes CSV files, also initiates values, and calls write_HTML() to return to the AJAX call
def write_CSV(query, amount):

	global html_output, first, file_name, num_key
	html_output = ""
	first = True
	
	# Call Youtube API
	results = youtube.search().list(q=query, part="snippet", type='video', maxResults=amount).execute()	
	# Create empty to list gather results
	collect = []
	date = datetime.datetime.now()
	# date = datetime.datetime.now(), format it
	date = str('{:%b %d, %Y at %I:%M%p}'.format(date))
	
	header = {'query': query, 'date': date}
	collect.append(dict(header))
	
	# Set counter
	c = 1
	file_no = 1
	# Set fieldnames
	fieldnames = ['Query', 'Date', 'Result', 'Video', 'Channel', 'Video Id', 'Published', 'Views', 'Likes', 'Comments']

			
	# Check if file exists before writing, need to account for the possiblity of having multiple files of the same query
	while os.path.isfile('csv/' + query + str(file_no).zfill(3) + '.csv'):
		file_no = int(file_no) + 1 

	# convert file number suffix to 3 digit, with leading zeros
	file_no = str(file_no).zfill(3)
	file_name = query + file_no + '.csv'
	
	with open('csv/' + file_name, 'w', newline='') as newfile:
		csv_writer = csv.DictWriter(newfile, fieldnames=fieldnames)
		csv_writer.writeheader()
		
		# Loop through Google data api list of dictionaries
		for item in results['items']:
			# Call function to receive data gathered by query using current videoId
			stats = get_stats(item['id']['videoId'])
			collect.append([
				c,
				item['snippet']['title'],
				item['snippet']['channelTitle'], 
				item['id']['videoId'],
				item['snippet']['publishedAt'],
				stats['viewCount'], 
				stats['likeCount'],
				stats['commentCount']
				])

			# call write_HTML which will create HTML string using API data gathered in the 'collect' list to send to client side
			write_HTML(False, collect)
			# write_HTML appends data from the last increment of the listm 'collect', which is passed as the argument. Need to clear for next loop. 
			collect.pop()
			# Write to CSV

			csv_writer.writerow({'Query': query, 'Date': date, 'Result': c, 'Video': item['snippet']['title'],
				'Channel': item['snippet']['channelTitle'], 'Video Id': item['id']['videoId'], 
				'Published': item['snippet']['publishedAt'], 'Views':stats['viewCount'], 'Likes': stats['likeCount'], 
				'Comments': stats['commentCount']})
			c += 1
	
	# write_HTML() finishes writing final lines to 'html_output'		
	write_HTML(True)
	
	html_output += "\n<input type=\"hidden\" class=\"hidden_val\" value=\"" + file_name + "\">"
	# return HTML string 
	## NEED SOME ERROR HANDLING?
	return jsonify({"response": True, "html": html_output})


@app.route('/download/<val>', methods=['GET'])
def download(val):

	uploads = os.path.join(app.config['UPLOAD'], val)

	# Send CSV file as attachment for download
	try:
		return send_file(uploads, as_attachment=True, attachment_filename=val, mimetype='text/csv')
		
	except:
		return "file not found"

# Handles the form submit from file size, server side validaton, returns the return of write_CSV 
@app.route('/query', methods=['POST'])
def validate():
	global html_output
	received = request.get_json()
	print(received)
	query = received['search']
	# make sure query is alpha/numerical or a space
	for char in list(query):
		if not char.isalnum() and not char.isspace():
			print("error 1")
			
	# Title case
	query.lower().capitalize()
	print(query)
	
	amount = received['size']
	if not amount.isdigit() and int(amount) < 11:
		print(2)
		return "error 2"

	clear_old_files()	
	return write_CSV(query, amount)


if __name__ == '__main__':
    app.run(debug=True)






