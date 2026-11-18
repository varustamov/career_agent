"""Capabilities refer to this application, not promises about third-party APIs."""
SOURCES = {
 'hh': {'name':'HeadHunter','search_mode':'public_api','apply_mode':'manual','oauth_available':False,'boards':False,'docs':'https://github.com/hhru/api','profile_url':'https://hh.ru/'},
 'greenhouse': {'name':'Greenhouse','search_mode':'company_board','apply_mode':'manual','oauth_available':False,'boards':True,'docs':'https://docs.greenhouse.io/job-board'},
 'lever': {'name':'Lever','search_mode':'company_board','apply_mode':'manual','oauth_available':False,'boards':True,'docs':'https://github.com/lever/postings-api'},
 'ashby': {'name':'Ashby','search_mode':'company_board','apply_mode':'manual','oauth_available':False,'boards':True,'docs':'https://developers.ashbyhq.com/docs/public-job-posting-api'},
 'smartrecruiters': {'name':'SmartRecruiters','search_mode':'company_board','apply_mode':'manual','oauth_available':False,'boards':True,'docs':'https://developers.smartrecruiters.com/docs/posting-api'},
 'remotive': {'name':'Remotive','search_mode':'public_api','apply_mode':'manual','oauth_available':False,'boards':False,'docs':'https://remotive.com/remote-jobs/api'},
 'arbeitnow': {'name':'Arbeitnow','search_mode':'public_api','apply_mode':'manual','oauth_available':False,'boards':False,'docs':'https://www.arbeitnow.com/blog/job-board-api'},
 'hackernews': {'name':'Hacker News','search_mode':'public_api','apply_mode':'manual','oauth_available':False,'boards':False,'docs':'https://github.com/HackerNews/API'},
}

# HH returned HTTP 403 in the tested environment. Keep its adapter and metadata
# for existing records while removing it from active search until revalidated.
ACTIVE_SOURCES = {key: value for key, value in SOURCES.items() if key != 'hh'}
