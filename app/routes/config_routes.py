from flask import Blueprint, render_template, request, redirect, url_for, flash
import yaml
import os

config_bp = Blueprint('config', __name__)

# Update the CONFIG_PATH to point to the root folder
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')

@config_bp.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        config_data = {
            'Database': {
                'username': request.form['db_username'],
                'password': request.form['db_password'],
                'host': request.form['db_host'],
                'database_name': request.form['db_name'],
                'track_modifications': request.form.get('db_track_modifications') == 'on'
            },
            'TMDb': {
                'api_key': request.form['tmdb_api_key']
            },
            'Secret_key': request.form['secret_key'],
            'qBittorrent': {
                'host': request.form['qb_host'],
                'username': request.form['qb_username'],
                'password': request.form['qb_password']
            },
            'Jackett': {
                'server_url': request.form['jackett_server_url'],
                'api_key': request.form['jackett_api_key'],
                'categories': {
                    'Movies': '2000',
                    'Music': '3000',
                    'TV': '5000'
                }
            },
            'Jellyfin': {
                'server_url': request.form['jellyfin_server_url'],
                'api_key': request.form['jellyfin_api_key']
            },
            'Spotify': {
                'client_id': request.form['spotify_client_id'],
                'client_secret': request.form['spotify_client_secret']
            }
        }

        try:
            with open(CONFIG_PATH, 'w') as file:
                yaml.dump(config_data, file, default_flow_style=False)
            flash('Configuration saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving configuration: {e}', 'danger')

        return redirect(url_for('config.config'))

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as file:
            config = yaml.safe_load(file)
    else:
        config = {}

    return render_template('config.html', config=config)