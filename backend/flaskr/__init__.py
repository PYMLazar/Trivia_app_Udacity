import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page',1,type==int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={'/':{'origins':"*"}})
 
    @app.route('/')
    def index():
      return 'Welcome to Trivia API'

    @app.after_request
    def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'Get, Post, Patch, Delete, Options')
      return response

   
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
        'total_categories': len(categories),
        'categories': categories_arr
      })

    @app.route('/questions', methods = ['GET'])
    def get_questions():
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
            #'questions': current_questions,
            #'totalquestions': len(Question.query.all())
            'total_questions': total_questions
          })
        except:
            abort(422)

    @app.route('/questions/create', methods=['POST'])
    def create_new_question():
        define_get = request.get_json()
        new_question = Question(
        question= request.json.get('question'),
        answer= request.json.get('answer'),
        difficulty= request.json.get('difficulty'),
        category= request.json.get('category')
        
      )
        new_question.insert()
        return jsonify({
            'success': True,
            'created' : new_question.id
        })

    @app.route('/questions/search', methods=['POST'])
    def search_term_question():
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
        except BaseException:
          abort(422)

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
      body = request.get_json()
      if not body:
        abort(400)
        previous_q = body['previous_questions']
        category_id = body['quiz_category']['id']
        #category_id = str(int(category_id) + 1)

      if category_id == 0:
        if previous_q is not None:
          questions = Question.query.filter(
          Question.id.notin_(previous_q)).all()
        else:
          questions = Question.query.all()
      else:
        if previous_q is not None:
          questions = Question.query.filter(
          Question.id.notin_(previous_q),
          Question.category == category_id).all()
        else:
          questions = Question.query.filter(
          Question.category == category_id).all()

          next_question = random.choice(questions).format()
          if not next_question:
            abort(404)
          if next_question is None:
            next_question = False

      return jsonify({
        'success': True,
        'question': next_question
      }) 

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





    