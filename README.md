# OctoPyTweet

This is a simple script to tweet stats and pictures for print jobs running on an OctoPrint print server. It is called from cron once a minute.
This would be better if it was an OctoPrint plug-in but what can you do. It works and I don't have time to learn how to make a plug-in right now.


# Installation
- On Twitter create a Twitter application and generate Twitter API Keys.
  Guides: 
  - https://themepacific.com/how-to-generate-api-key-consumer-token-access-key-for-twitter-oauth/994/
  - https://dev.twitter.com/oauth/overview/application-owner-access-tokens
  
- Copy config.cfg.sample to config.cfg.

- Edit config.cfg and replace settings with real values.

- Create a cronjob that runs OctoPyTweet.py once a minute.
