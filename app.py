from flask import Flask, render_template, redirect, request, session, jsonify
import praw
import random

NO_OF_ROUNDS = 10
SUBREDDITS = [
  'wholesomememes', \
  'bikinibottomtwitter', \
  'funny', \
  'pics', \
]

# APIs
app = Flask(__name__)
app.config.from_object('config.Default')
app.config.from_object('config.Reddit')

reddit = praw.Reddit(
  client_id = app.config['R_ID'],
  client_secret = app.config['R_SECRET'],
  username = app.config['R_USER'],
  password = app.config['R_PASS'],
  user_agent = 'reddit_rater@py_script',
)

# funcs
def get_top_submissions_gen(subreddit, limit):
  return reddit \
    .subreddit(subreddit) \
    .top(time_filter = 'day', limit = limit) \

def create_submission(id, title, url, permalink, score):
  return {
    'id': id, \
    'title': title, \
    'url': url, \
    'permalink': permalink, \
    'score': score, \
  }

def get_top_submissions(subreddit, limit, no_videos):
  submissions = []

  for submission in get_top_submissions_gen(subreddit, limit + 10):
    if no_videos and ('video' in submission.url or len(submissions) == limit):
      break

    submissions.append(create_submission(
      submission.id, \
      submission.title, \
      submission.url, \
      submission.permalink, \
      submission.score, \
    ))
  
  return submissions

def calc_guess_score(guess, actual):
  accuracy = float(guess) / actual
  if accuracy > 1:
    accuracy = 1 / float(accuracy)

  return int(round(float(accuracy) * 100))

# Routes
@app.route('/', methods=['GET', 'POST', 'DELETE'])
def index():
  submissions = session.get('submissions', get_top_submissions(
    subreddit = random.choice(SUBREDDITS), \
    limit = NO_OF_ROUNDS, \
    no_videos = True, \
  ))
  session['submissions'] = submissions
  score = session.get('score', 0)
  round_no = session.get('round_no', 1)
  rounds_remaining = NO_OF_ROUNDS - round_no

  if request.method == 'POST':
    guess = request.form.get('score')
    actual = submissions[round_no - 1]['score']
    score += calc_guess_score(int(guess), int(actual))
    session['score'] = score
    round_no += 1
    session['round_no'] = round_no

    return render_template('check.html',
      current_submission = submissions[round_no - 2], \
      guess = guess, \
      actual = actual, \
      score = score, \
      round_no = round_no - 1, \
      rounds_remaining = rounds_remaining, \
    )

  elif request.method == 'DELETE':
    session['submissions'] =  get_top_submissions(
      subreddit = random.choice(SUBREDDITS), \
      limit = NO_OF_ROUNDS, \
      no_videos = True, \
    )
    session['score'] = 0
    session['round_no'] = 1

    return 'done'

  if round_no == 11:
    return render_template('done.html',
      current_submission = submissions[round_no - 2], \
      round_no = round_no - 1, \
      score = score, \
    )

  return render_template('index.html',
    current_submission = submissions[round_no - 1], \
    round_no = round_no, \
    score = score, \
    rounds_remaining = rounds_remaining, \
  )


# Run Flask
if __name__ == '__main__':
  app.run()
