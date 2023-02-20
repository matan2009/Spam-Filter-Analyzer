# Spam-Filter-Analyzer

Spam Filter Analyzer is a tool(script) that runs spam filtering service over some mails that placed in a folder and save metadata to a csv result file, only for mails that were detected as spam by the spam service.

## Dependencies:

requirements.txt file is attached for this submission. 

## How to run the script:

"script path" "Mails folder path" "Threshold" "Spam service IP and port" "CSV path"

Running example: spam_filter_analyzer.py C:\Users\user\Desktop\spam_assassin\mails 1 52.166.235.37:783 C:\Users\user\Desktop\spam_assassin\output_result

## Script's flow and process:
1.	The script creates CSV result file.
2.	Writes headers to the result file.
3.	Extracts metadata from mails using Pool object. 
4.  For each mail the script sends a request for the spam service, and stores the response (The score it got 	from the spam filtering service).
5.  If the score is greater (or equal) to the input threshold, it will continue to extract more interesting 	metadata from the spam email.
6.  The following fields (metadata) will be added for each spam email to the result file:
  - mail file name
  -	mail subject
  -	sender name
  -	sender address
  -	recipient address
  -	spam-assassin score
  -	number of attachments
  -	attachments file names
  -	list of links
  -	number of links
  -	the date that the mail was received
