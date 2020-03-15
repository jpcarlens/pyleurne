from flask import Flask, url_for, escape, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit

import namegenerator

from app.models.rooms import *
from app.models.user import *
from app.models.roles import *

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
socket_io = SocketIO(app)

room_manager = RoomManager()
sockets_rooms = {}


@app.route('/')
def show_index():
    generated_pseudo = namegenerator.gen()
    user_ip_address = request.remote_addr
    user = User(generated_pseudo, user_ip_address, Roles.CREATOR)

    generated_room_id = room_manager.add_new_room__(user)
    print("Création de la room %d." % generated_room_id, end="\n\n")

    return redirect(url_for('show_room_page', room_id=generated_room_id))


@app.route('/rooms/<int:room_id>')
def show_room_page(room_id):
    if room_manager.check_room(room_id) is False:
        print("Un user a tenté d'accéder a une room inexistante (%d). Redirection vers la racine..." % room_id,
              end="\n\n")
        return redirect(url_for('show_index'))

    current_user = connect_to_existing_room(room_id, request.remote_addr)

    room_users = room_manager.get_room_list()[room_id].get_userlist()

    template_args = {'style_index_url': url_for('static', filename='styles/index.css'),
                     'scripts_index_url': url_for('static', filename='scripts/index.js'),
                     'default_user_img': url_for('static', filename='res/img/defaultUser.png'),
                     'users': room_users,
                     'current_user': current_user,
                     'roomID': room_id
                     }

    return render_template('index.html', template_args=template_args)


@app.route('/rooms/<int:room_id>/population')
def give_room_population(room_id):
    json_str = room_manager.get_room_list()[room_id].get_json_username_list()
    return jsonify(json_str)


def connect_to_existing_room(room_id, ip_address):
    user = None
    if not room_manager.get_room_list()[room_id].get_creator_connected_state():
        user = room_manager.get_room_list()[room_id].get_creator()
        room_manager.get_room_list()[room_id].set_creator_connected_state(True)
    else:
        pseudo = namegenerator.gen()
        user = User(pseudo, ip_address, Roles.LAMBDA)
        room_manager.get_room_list()[room_id].add_new_user(user)

    print("Nouvelle connection à la room {%s} : login[%s] - ip[%s] - role[%s]" % (
    str(room_id), user.get_pseudo(), user.get_ip_address(), user.get_role().name))
    return user


''' PARTIE ACCUEIL DES SOCKETS '''


@socket_io.on('message')
def new_socket_connection_handler(message):
    str = "Message réçu d'un socket -> " + message
    print(str, end="\n\n")
    emit('reponse', str)


@socket_io.on('json')
def handle_socket_json(json):
    print("json reçu d'un socket -> \n" + str(json), end="\n\n")


@socket_io.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print("\t\t -> (%s) connecté à la room de sockets (%s) " % (username, room), end="\n\n")
    emit('join', 'Vous rejoignez la room %s' % room)

    if room not in sockets_rooms:
        sockets_rooms[room] = []
        sockets_rooms[room].append(username)
    else:
        sockets_rooms[room].append(username)

    tell_to_users_to_update_userlist(room)


def tell_to_users_to_update_userlist(room):
    emit('clear', 'clear the div', room=room)

    for i in sockets_rooms[room]:
        emit('appendUser', (i, url_for('static', filename='res/img/defaultUser.png')), room=room)


''' PARTIE AJOUT DE VIDEO '''


@socket_io.on('videoAddRequest')
def handle_video_add_request(data):
    print("Demande d'ajout de vidéo reçue. Voici les détails :", end="\n\t")
    print("username[%s]" % data['username'], "room[%s]" % data['room'],"videoURL[%s]" % data['videoURL'], sep="\n\t")
    emit('reponse', 'Demande reçue l\'ami.')
    print("Tentative de recherche de l'utilisateur")
    print("\tsocketUser[%s] -- roomCreator[%s]" % (data['username'],room_manager.get_room_list()[int(data['room'])].get_creator().get_pseudo()))