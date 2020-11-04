import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

#Define constant (questions) for maximum
QUESTIONS_PER_PAGE = 10

# The helper method paginate_questions will include the request and the selection
# This will benifit the speed (prevents slow down on request) of the data and also an clear overview.
# Get the value of the key page from the arguments(off the request).
# Sets the default of value to 1 (if not exist) of type integer

def paginate_questions(request, selection):
    page = request.args.get('page',1,type==int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions

def create_app(test_config=None):
    # create and configure the app (Any orgin (*) can access the URI endpoint)
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={'/':{'origins':"*"}})
 
    @app.route('/')
    def index():
      return 'Welcome to Trivia API'

    # This allows a list of HTTP methods (Get,Post etc) and headers to be accessed.
    # After the request has been received the method will run and add some headers in the response.
  
    @app.after_request
    def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'Get, Post, Patch, Delete, Options')
      return response

    # Gets all the categories (id and type) (order by id) and format them with the method 
    # defined correctly for JSON response.Abort 404 will check for length of categories (outofrange).

    @app.route('/categories', methods = ['GET'])
    def retrieve_categories():
      categories = Category.query.order_by(Category.id).all()
      if len(categories) == 0:
        abort(404)
      else:
        categories = Category.query.all()
        categories_arr = {}
      for category in categories:
        categories_arr [category.id] = category.type
      return jsonify({
        'success': True,
        'category': [category.format() for category in categories],
        'categories': categories_arr,
        'total_categories': len(categories)
      })
    
    # Gets all the questions/categories and used Flask pagination (max-10 and format them with the method 
    # defined correctly for JSON response.

    @app.route('/questions', methods = ['GET'])
    def retrieve_questions():
        questions = Question.query.all()
        page = request.args.get('page', 1, type =int)
        start = (page - 1) * 10
        end = start + 10
        formatted_qs = [q.format() for q in questions]
        curr_catgs = []
    
        for q in formatted_qs[start:end]:
          cat_name = q['category'] 
          if cat_name not in curr_catgs:
            curr_catgs.append(cat_name)
        
        categories = Category.query.all()
        categories_arr = {}
        for category in categories:
            categories_arr[category.id] = category.type

        return jsonify({
          'success' : True,
          'questions' : formatted_qs[start:end],
          'total_questions' : len(formatted_qs),
          'categories' : categories_arr
        })
    #T he variable name question_id is given and after will check if the question exist, 
    # if not abort (404), otherwise it will be deleted and then the app will show the selection
    # of questions using pagination    

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
          question = Question.query.filter(Question.id == question_id).one_or_none()
          if question is None:
            abort(404)
          else:
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            total_questions = len(selection)
          return jsonify({
            'success': True,
            'deleted': question_id,
            'questions': current_questions,
            'total_questions': total_questions
          })
        except:
            abort(422)

    # This will add an question to the app(database).First we will get the body from the request. From that
    # we get several data items (question, answer etc).

    @app.route('/questions/create', methods=['POST'])
    def create_question():
        body = request.get_json()
        
        new_question= body.get('question', None)
        new_answer= body.get('answer', None)
        new_difficulty= body.get('difficulty',None)
        new_category= body.get('category',None)    

        try:
          question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
          question.insert()

          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
            'success': True,
            'created' : question.id,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
           })
        except:
          abort(422)

    #This will have the ability to query for any phrase (case insensitive) 
    # in the questions. It will then paginate the results. It will throw an error 404
    # if anything wasn't able to be processed.

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm', None)

        try:
            if search_term:
              selection = Question.query.order_by(Question.id).filter(
              Question.question.ilike('%{}%'.format(search_term)))
              current_questions = paginate_questions(request, selection)

              return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection.all()), 
                'current_category': None
              })
        except:
          abort(404)

    # This will get all the questions based on category by providing the 
    # variable name in the app route (category_id (integer type)), This will be passed
    # as an parameter to the method. The forein key category in questions will be checked
    # against the id (key) from categories. Based on this selection it will results 
    # in an pagination output where each category will show the corresponding questions.

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        try:
          selection = Question.query.filter(
            Question.category == category_id).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'current_category': category_id
          })
        except:
          abort(422)

    #This enpoint will have two elements:category and previous question and will
    #return random questions from the selected category.After an answer the app
    #(frontend will render for the next question). 

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
      body = request.get_json()
      prev_questions =body.get('previous_questions', [])
      quiz_category = body.get('quiz_category', None)

      try:
        if quiz_category['id'] == 0:
          quiz = Question.query.all()
        else:
          quiz = Question.query.filter_by(category=quiz_category['id']).all()
        if not quiz:
          return abort(422)
        selected = []
        for question in quiz:
          if question.id not in prev_questions:   
            selected.append(question.format())         
        if len(selected) != 0:
          result = random.choice(selected)
          return jsonify({
            'success': True,
            'question':result
          })
        else:
          return jsonify({
            'success': False,
            'question':None
          })
      except:
        abort(422)

      #This are the error handlers for the endpoints and wil handle the error 
      #if applicable.
      @app.errorhandler(404)
      def not_found(error):
          return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
          }), 404

      @app.errorhandler(422)
      def unprocessable(error):
          return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
          }), 422

      @app.errorhandler(400)
      def bad_request(error):
          return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
          }), 400

    return app





    