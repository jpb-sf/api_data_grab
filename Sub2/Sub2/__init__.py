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
@app.route('/error/<error>')
def error(error='API'):
    if error == 'js.html':
        message1 = "It looks like your Javascript is disabled. This application will not run properly without it."
        message2 = "Please enable Javascript, and refresh site to access the application's features!" 
    elif error == 'API':
        message1 = "It looks like there is an issue getting data from YouTube's API."
        message2 = "Please try submitting your query again or try back later. We apoligize for any inconvenience."
    else:
        return redirect('/')

    return render_template('disabled.html', message1=message1, message2=message2)

# Clear user created csv file when user clicks from display back to search or home.
@app.route('/clear/<file>', methods=['GET'])
def clear(file):
    print('file to clear is ' + file)
    try:
        f = open(basedir + '/csv/' + file, 'w')
    except Exception as e:
        print('error clearing file')
    else:
        os.remove(f.name)
        return "True"

# Function returns the age of a file measured in hours (whole integers)
def get_file_age(filepath):
    # time.time() method is time returned in seconds
    # getmtime() method in Python is used to get the time of LAST modification of the specified path
    return int(((time.time() - os.path.getmtime(basedir + '/csv/' + filepath)) / 60) / 60)

# Loops through server's csv directory, and deletes any user-created csv files older than 2 hours (handles any activity where user closes browser window)
def clear_old_files():
    for f in os.listdir(basedir + '/csv/'):
        # If file is older than 2 hours
        if get_file_age(f) > 2:
            open_f = open(basedir + '/csv/' + f, 'w')
            os.remove(open_f.name)
            return "True"

# Support function that makes additional API call for data of (viewCount, likeCount, commentCount)
def get_stats(videoId):
    try:
        # Call Youtube Api
        stats = youtube.videos().list(id=videoId, part="statistics").execute()
    
    except Exception as e:
        print(e)
        error="API"
        return redirect(url_for('error', error=error))

    else:
        # Put results into string
        results = {
        'viewCount': stats['items'][0]['statistics']['viewCount'], 
        'likeCount': stats['items'][0]['statistics']['likeCount'],
        'commentCount': stats['items'][0]['statistics']['commentCount'],
        }
        return results

# writes CSV file, and gathers data in a list to send back to client/html template (populates jinja values)

def retrieve_query(query, amount):
    global html_output, first, file_name, num_key
    # Flag variable
    first = True
     # Call Youtube API
    try:
        results = youtube.search().list(q=query, part="snippet", type='video', maxResults=amount).execute()

    except Exception as e:
        print(e)
        error="API"
        return redirect(url_for('error', error=error))
    
    date = datetime.datetime.now()
    # Format the date
    date = str('{:%b %d, %Y at %I:%M%p}'.format(date))
    
    # Set counter
    result_no = 1
    file_no = 1
    # Set fieldnames
    fieldnames = ['Query', 'Date', 'Result', 'Video', 'Channel', 'Video Id', 'Published', 'Views', 'Likes', 'Comments']

    # Check if file exists before writing, need to account for the possiblity of having multiple files of the same query
    while os.path.isfile(basedir + '/csv/' + query + str(file_no).zfill(3) + '.csv'):
        # Increment file name by 1
        file_no = int(file_no) + 1 

    # convert file number suffix to 3 digit, with leading zeros
    file_no = str(file_no).zfill(3)
    file_name = query + file_no + '.csv'
    
    header = {'query': query, 'date': date}
    
    with open(basedir + '/csv/' + file_name, 'w+', newline='', encoding="utf-8") as newfile:
        
        csv_writer = csv.DictWriter(newfile, fieldnames=fieldnames)
        csv_writer.writeheader()
        # Create empty list to gather results
        collect = [] 
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

            csv_writer.writerow({'Query': query, 'Date': date, 'Result': result_no, 'Video': item['snippet']['title'],
                'Channel': item['snippet']['channelTitle'], 'Video Id': item['id']['videoId'], 
                'Published': item['snippet']['publishedAt'], 'Views':stats['viewCount'], 'Likes': stats['likeCount'], 
                'Comments': stats['commentCount']})
            result_no += 1
    
    # ## NEED SOME ERROR HANDLING?
    # return jsonify({"response": True, "html": html_output})
    column_titles = ["#", "Video Title", "Channel", "Video ID", "Published on", "Views", "Likes", "Comments"]
    return render_template('query.html', header=header, collect=collect, columnTitles=column_titles, fileName = file_name)

@app.route('/download/<val>', methods=['GET'])
def download(val):
    uploads = os.path.join(app.config['UPLOAD'], val)
    # Send CSV file as attachment for download
    try:
        return send_file(uploads, as_attachment=True, attachment_filename=val, mimetype='text/csv')
        
    except Exception as e:
        print(e)

# Handles the form submit from file size, server side validaton, returns the return value of write_csv 
@app.route('/query')
def validate():
    # received = request.get_json()
    query = request.args.get('query')
    amount = request.args.get('amount')
    # Catch manual manipulation to url 'amount' paramter
    print(amount)
    try:
        int(amount)
        if int(amount) > 11:
            raise ValueError
    except ValueError as e:
        print(e)
        error = "Looks like there was an error. Please enter a result number between 1 and 11."
        return render_template('index.html', error=error)
    
    # Checks for old queries (csv files) and deletes them
    try:
        clear_old_files()
    except Exception as e:
        print(e)
    finally:   
        return retrieve_query(query, amount)

if __name__ == '__main__':
    app.run(debug=True)

