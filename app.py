#!/usr/bin/env python3
"""
LinkedIn Content Creation Agent
A tool to generate LinkedIn posts in the style of Nikit Bassi
"""

import sys
import os
import json
from flask import Flask, render_template, request, jsonify
from src.content_input import ContentInput
from src.post_generator import PostGenerator
from src.auto_research import AutoResearch
from src.additional_features import HashtagResearch, ContentCalendar
from src.utils import init_database, get_posts, load_config

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize components
content_input = ContentInput()

@app.route('/')
def index():
    """Main dashboard"""
    posts = get_posts(limit=10)
    return render_template('index.html', posts=posts)

@app.route('/api/generate-post', methods=['POST'])
def generate_post():
    """API endpoint to generate a post from user input"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        context = data.get('context', '').strip()
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        result = content_input.process_user_input(topic, context if context else None)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-research', methods=['POST'])
def auto_research():
    """API endpoint to start auto-research workflow"""
    try:
        data = request.json
        num_ideas = data.get('num_ideas', 5)
        
        result = content_input.process_auto_research(num_ideas)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-generate', methods=['POST'])
def auto_generate():
    """API endpoint to auto-generate posts from topics"""
    try:
        data = request.json
        limit = data.get('limit', 5)
        
        result = content_input.auto_generate_posts_from_ideas(limit)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts', methods=['GET'])
def list_posts():
    """Get all generated posts"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        
        posts = get_posts(status=status, limit=limit)
        
        return jsonify({'posts': posts, 'count': len(posts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hashtag-suggestions', methods=['POST'])
def hashtag_suggestions():
    """Get hashtag suggestions for a topic"""
    try:
        data = request.json
        topic = data.get('topic', '')
        content = data.get('content', '')
        
        hashtags = HashtagResearch.suggest_hashtags(topic, content, num_suggestions=8)
        analysis = HashtagResearch.validate_hashtags(hashtags)
        
        return jsonify({
            'hashtags': hashtags,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/content-calendar', methods=['GET'])
def content_calendar():
    """Get content calendar view"""
    try:
        posts = get_posts(limit=100)
        calendar = ContentCalendar.get_calendar_view(posts)
        distribution = ContentCalendar.analyze_content_distribution(posts)
        schedule = ContentCalendar.suggest_posting_schedule(posts)
        
        return jsonify({
            'calendar': calendar,
            'distribution': distribution,
            'schedule': schedule
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly-plan', methods=['GET'])
def monthly_plan():
    """Get monthly content plan"""
    try:
        num_posts = int(request.args.get('num_posts', 20))
        plan = ContentCalendar.generate_monthly_plan(num_posts)
        
        return jsonify(plan)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trending-hashtags', methods=['GET'])
def trending_hashtags():
    """Get trending hashtags by category"""
    try:
        hashtags = HashtagResearch.get_trending_hashtags_in_niche()
        
        return jsonify(hashtags)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration status"""
    try:
        config = load_config()
        
        status = {
            'openai_configured': bool(config.get('openai_api_key') and 
                                     config.get('openai_api_key') != 'YOUR_OPENAI_API_KEY'),
            'newsapi_configured': bool(config.get('newsapi_key') and 
                                      config.get('newsapi_key') != 'YOUR_NEWSAPI_KEY'),
            'research_topics': len(config.get('research_topics', []))
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main entry point"""
    # Initialize database
    init_database()
    
    print("\n" + "="*60)
    print("LinkedIn Content Creation Agent")
    print("="*60)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--cli':
            # Interactive CLI mode
            content_input.interactive_workflow()
        elif sys.argv[1] == '--web':
            # Web server mode
            print("\n🌐 Starting web server...")
            print("📍 Open http://localhost:5000 in your browser")
            print("\nPress Ctrl+C to stop the server\n")
            
            app.run(debug=True, port=5000)
        elif sys.argv[1] == '--help':
            print_help()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print_help()
    else:
        # Default: interactive mode
        content_input.interactive_workflow()

def print_help():
    """Print help message"""
    print("""
Usage: python app.py [OPTIONS]

Options:
    --cli       Run in interactive CLI mode
    --web       Start web server (http://localhost:5000)
    --help      Show this help message

Examples:
    python app.py --cli      # Interactive CLI
    python app.py --web      # Web interface
    python app.py            # Default (CLI mode)

Configuration:
    Edit config/config.json to add:
    - OpenAI API key
    - NewsAPI key (for auto-research)

""")

if __name__ == '__main__':
    main()
