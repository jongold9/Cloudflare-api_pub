from flask import Flask, render_template, redirect, url_for, flash, session, request
import requests
from datetime import datetime
from config import USERS, ACCOUNTS

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def load_accounts():
    return ACCOUNTS

def log_user_action(username, action, domain=None):
    with open('user_log.txt', 'a') as log_file:
        time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if domain:
            log_file.write(f"{time_stamp} - {username} performed {action} on domain {domain}\n")
        else:
            log_file.write(f"{time_stamp} - {username} performed {action}\n")

def get_zones(account):
    url = "https://api.cloudflare.com/client/v4/zones"
    zones = []
    headers = {
        "Authorization": f"Bearer {account['API_KEY']}",
        "Content-Type": "application/json"
    }
    
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page, 'per_page': 50})
        if response.status_code == 200:
            data = response.json()
            zones.extend(data['result'])
            if page >= data['result_info']['total_pages']:
                break
            page += 1
        else:
            print(f"Error getting zones for {account['EMAIL']}: ", response.json())
            break

    return zones

def purge_cache(zone_id, account):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    headers = {
        "Authorization": f"Bearer {account['API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {"purge_everything": True}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.json()

@app.route('/')
def index():
    if 'username' in session:
        accounts = load_accounts()
        return render_template('index.html', accounts=accounts)
    return redirect(url_for('login'))

@app.route('/search', methods=['POST'])
def search():
    domain = request.form['domain'].strip().lower()
    accounts = load_accounts()
    results = []
    
    print(f"Searching for domain: '{domain}'")
    for account in accounts:
        print(f"Checking account: {account['name']}")
        zones = get_zones(account)
        print(f"Retrieved zones for account '{account['name']}': {[zone['name'] for zone in zones]}")
        
        for zone in zones:
            print(f"Comparing with zone: '{zone['name'].lower()}'")
            if zone['name'].lower() == domain:
                results.append((account['name'], zone['id'], zone['name']))

    if not results:
        flash(f"No zones found for domain '{domain}'", "info")
        print(f"No matching zones found for '{domain}' in any account.")
    else:
        print(f"Found zones: {results}")

    return render_template('results.html', results=results, domain=domain)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USERS and password == USERS[username]:
            session['username'] = username
            log_user_action(username, "logged in")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    log_user_action(session['username'], "logged out")
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/purge/<zone_name>/<account_name>', methods=['POST'])
def purge(zone_name, account_name):
    accounts = load_accounts()
    account = next((acc for acc in accounts if acc['name'] == account_name), None)
    
    if account:
        zones = get_zones(account)
        zone = next((z for z in zones if z['name'] == zone_name), None)
        
        if zone:
            zone_id = zone['id']
            success, response = purge_cache(zone_id, account)

            if success:
                flash(f"Cache successfully cleared for domain {zone_name}", "success")
                log_user_action(session['username'], "cleared cache", domain=zone_name)
            else:
                flash(f"Error clearing cache for domain {zone_name}: {response['errors'][0]['message']}", "error")
        else:
            flash(f"Zone for domain {zone_name} not found", "error")
    else:
        flash("Account not found", "error")

    return redirect(url_for('index'))

# очистка кеша всех доменов в аккаунте
@app.route('/purge_all/<account_name>', methods=['POST'])
def purge_all(account_name):
    accounts = load_accounts()
    account = next((acc for acc in accounts if acc['name'] == account_name), None)

    if account:
        zones = get_zones(account)
        if not zones:
            flash(f"No zones found for account {account_name}.", "info")
            return redirect(url_for('index'))

        success_count = 0
        error_count = 0
        for zone in zones:
            success, response = purge_cache(zone['id'], account)
            if success:
                success_count += 1
            else:
                error_count += 1

        flash(
            f"Cache cleared for {success_count} zones in account {account_name}. Errors: {error_count}.",
            "success" if success_count > 0 else "error"
        )
    else:
        flash(f"Account {account_name} not found.", "error")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

