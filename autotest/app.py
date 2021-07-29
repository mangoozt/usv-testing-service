from flask import Flask, request, Response, send_from_directory

# from flask_cors import cross_origin, CORS

app = Flask(__name__)


# @app.route("/", defaults={'path': ''})
# def serve(path):
#     return send_from_directory(app.static_folder, 'index.html')


# @cross_origin()
@app.route('/github/payload', methods=['POST'])
def playload():
    json = request.get_json()
    print(json)

    return Response(request.get_data(), mimetype='text/plain')


# @cross_origin()
@app.route('/api/v1/takeOff')
def takeOff():
    return Response('ok', mimetype='text/plain')


# @cross_origin()
@app.route('/api/v1/land')
def land():
    return Response('ok', mimetype='text/plain')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8001)
