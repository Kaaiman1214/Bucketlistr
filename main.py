import os

from website import create_app

app = create_app()

if __name__ == '__main__':
    if os.environ.get('BUCKETLIST_DEBUG') == '1':
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app,
              host=os.environ.get('BUCKETLIST_HOST', '127.0.0.1'),
              port=int(os.environ.get('BUCKETLIST_PORT', '5000')))
