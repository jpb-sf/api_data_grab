from apiclient.discovery import build
import os
import time
import re
import random
import datetime
import csv
from flask import Flask, request, session, url_for, flash, redirect, render_template, json, jsonify, send_from_directory, send_file
import json
import datetime
import requests
import config

#=============================================================================

# # Initiate app
app = Flask(__name__)
app.config.from_object('config.Development')

# .env file
api_key = config.Development.API_KEY

# # google api
youtube = build('youtube', 'v3', developerKey=api_key, cache_discovery=False)

basedir = os.path.abspath(os.path.dirname(__file__))

@app.errorhandler(404)
def internal_error(error):
	return render_template('index.html')

# Start App
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# Send message to user on client side if scripting is turned off
@app.route('/error')
def error():
    return render_template('disabled.html')

# Clear user created csv file when user clicks from display back to search or home.
@app.route('/clear/<file>', methods=['GET'])
def clear(file):
	print('file to clear is ' + file)
	try:
		f = open('csv/' + file, 'w')
		os.remove(f.name)
		return 'True'
	except Exception as e:
		print('error clearing file')
		return 'False'

# Function returns the age of a file measured in hours (whole integers)
def get_file_age(filepath):
	# time.time() method time returned in seconds
	# getmtime() method in Python is used to get the time of last modification of the specified path
	return int(((time.time() - os.path.getmtime('csv/' + filepath)) / 60) / 60)

# Loops through server's csv directory, and deletes any user-created csv files older than 2 hours (handles any activity where user closes browser window)
def clear_old_files():
	try:
		for f in os.listdir('csv/'):
			# If file is older than 2 hours
			if get_file_age(f) > 2:
				open_f = open('csv/' + f, 'w')
				os.remove(open_f.name)
	except Exception as e:
		print('error clearing old file')
		return 'False'

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
def write_html(final, *args):
	
	args = list(*args)
	global first, html_output

	column_titles = ["#", "Video Title", "Channel", "Video ID", "Published on", "Views", "Likes", "Comments"] 

	# final true value adds closing tags to HTML string, (writes html buttons)
	if final == True:
		html_output += "</table>\n" \
		 + "<button type=\"button\" onclick=\"home()\" class=\"button mt-1\">Search</button>\n" \
		 + "<button type=\"button\" onclick=\"download()\"class=\"button mt-1\">Download</button>\n" 
		return
	
	# If first call of function, write the header text, and header row
	if first:
		html_output += "<h4><i>Query:\"" + args[0]['query'] + "\" | On: " + args[0]['date'] +" PST</i></h4>\n"  \
		+ "<table class=\"table\">\n" \
		+ "<tr class=\"head\">\n" 
		
		# Loop through column titles and add
		c = 0	
		for i in column_titles:
			c += 1
			html_output += "\t<th class=\"cell cell" + str(c)+ "\">" + i + "</th>\n"
		html_output += "</tr>\n" 
	
	first = False

	html_output += "<tr class=\"row\">\n" 
	
	c = 0
	# add table data cells to row of html string
	for item in args[1]:
		c += 1
		html_output += "\t<td class=\"cell cell" + str(c) + "\">" + str(item) + "</td>\n"
	html_output += "</tr>\n"


# writes CSV files, also initiates values, and calls write_html() to return to the AJAX call
def write_csv(query, amount):

	global html_output, first, file_name, num_key
	html_output = ""
	# Flag variable
	first = True
	
	# Call Youtube API
	results = youtube.search().list(q=query, part="snippet", type='video', maxResults=amount).execute()	
	# Create empty list to gather results
	date = datetime.datetime.now()
	# date = datetime.datetime.now(), format the date
	date = str('{:%b %d, %Y at %I:%M%p}'.format(date))
	
	header = {'query': query, 'date': date}
	collect = []
	collect.append(dict(header))
	
	# Set counter
	result_no = 1
	file_no = 1
	# Set fieldnames
	fieldnames = ['Query', 'Date', 'Result', 'Video', 'Channel', 'Video Id', 'Published', 'Views', 'Likes', 'Comments']

	# Check if file exists before writing, need to account for the possiblity of having multiple files of the same query
	while os.path.isfile('csv/' + query + str(file_no).zfill(3) + '.csv'):
		# Increment file name by 1
		file_no = int(file_no) + 1 

	# convert file number suffix to 3 digit, with leading zeros
	file_no = str(file_no).zfill(3)
	file_name = query + file_no + '.csv'
	
	with open(basedir + '/csv/' + file_name, 'w+', newline='') as newfile:
		csv_writer = csv.DictWriter(newfile, fieldnames=fieldnames)
		csv_writer.writeheader()
		
		# Loop through Google data api list of dictionaries
		for item in results['items']:
			# Call function to receive data gathered by query using current videoId
			stats = get_stats(item['id']['videoId'])
			# Add query results as a list 
			collect.append([
				result_no,
				item['snippet']['title'],
				item['snippet']['channelTitle'], 
				item['id']['videoId'],
				item['snippet']['publishedAt'],
				stats['viewCount'], 
				stats['likeCount'],
				stats['commentCount']
				])

			# Call write_html() which will create HTML string using API data gathered in the 'collect' list to send to client side
			write_html(False, collect)
			# Since write_html() appends data from the last index (a dict) in the list 'collect', which is passed as the argument. The last index now needs to be removed-- pop(), for the next cycle of the loop
			collect.pop()
			# Write to CSV

			csv_writer.writerow({'Query': query, 'Date': date, 'Result': result_no, 'Video': item['snippet']['title'],
				'Channel': item['snippet']['channelTitle'], 'Video Id': item['id']['videoId'], 
				'Published': item['snippet']['publishedAt'], 'Views':stats['viewCount'], 'Likes': stats['likeCount'], 
				'Comments': stats['commentCount']})
			result_no += 1
	
	# write_html() finishes writing final lines to 'html_output'		
	write_html(True)
	
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

# Handles the form submit from file size, server side validaton, returns the return value of write_csv 
@app.route('/query/', methods=['GET'])
def validate():
	global html_output
	# received = request.get_json()
	query = request.args.get('query')
	amount = request.args.get('amount')
	
	if not amount.isdigit() and int(amount) < 11:
		print(2)

	# Checks for old queries (csv files) and deletes them
	clear_old_files()	
	return write_csv(query, amount)


if __name__ == '__main__':
    app.run(debug=True)






