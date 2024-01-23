# Flask is a library that allows you to create websites in Python
import os

import requests
from flask import Flask, render_template, session, redirect, request, url_for
import csv
import random
# Allows you to sort a list of lists by the inner list
from operator import itemgetter
from openai import OpenAI
import time

# Flask syntax
app = Flask(__name__)
OPENAI_API_KEY = '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'
client = OpenAI(api_key=OPENAI_API_KEY)


app.secret_key = "12345"
PASSPHRASE = "talha"

def update_elo(a, b):
    # We will assume the first parameter a is the item that wins
    # Suppose Player 1 wins: rating1 = rating1 + k*(actual – expected)
    # The expectation of Player 1 winning is given by the formula:
    # P1 = (1.0 / (1.0 + 10^((b-a) / 400)))
    # We will set k to 30 for the time being
    k = 30
    return a + k*(1 - (1 / (1 + (10**((b-a) / 400))))), b + k*(0 - (1 / (1 + (10**((a-b) / 400)))))


# Let's create a list of lists which will look like this:
# [[name, price, link, elo], [name2, price2, link2, elo2], etc...]
elo = 1400 # This is the starting elo for all items
items = []
with open('ebay_active_items.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        name_price_link_elo_image = []
        name = row[0].split(',')[0]
        price = row[0].split(',')[1]
        link = row[0].split(',')[2]
        name_price_link_elo_image.append(name)
        name_price_link_elo_image.append(price)
        name_price_link_elo_image.append(link)
        name_price_link_elo_image.append(elo)

        # Generate AI images for each item
        prompt1 = name
        directory = 'static'
        image_exists = False
        for filename in os.listdir(directory):
            if filename.endswith('.jpg'):
                with open(os.path.join(directory, filename)) as f:
                    if prompt1 in f.name:
                        image_exists = True
        if not image_exists:

            response1 = client.images.generate(
                model="dall-e-2",
                prompt=prompt1,
                size="256x256",
                quality="standard",
                n=1,
            )
            image_url1 = response1.data[0].url
            print(image_url1)
            img_data = requests.get(image_url1).content
            with open('images/' + name + '.jpg', 'wb') as handler:
                handler.write(img_data)
            time.sleep(12)
        items.append(name_price_link_elo_image)


@app.route('/')
def show_pair_of_items():
    random_value_1 = random.randint(1, len(items)-1)
    random_value_2 = random.randint(1, len(items)-1)
    session['item1'] = items[random_value_1]
    session['item2'] = items[random_value_2]

    return render_template('index.html',
                           contestant1=str(items[random_value_1][0]),
                           image_url1=url_for('static', filename=items[random_value_1][0] + '.jpg'),
                           contestant2=str(items[random_value_2][0]),
                           image_url2=url_for('static', filename=items[random_value_2][0] + '.jpg'),
                           price1='£' + str(items[random_value_1][1]),
                           price2='£' + str(items[random_value_2][1])
                           )


@app.route('/1')
def item_one_wins():
    item1 = session['item1']
    item2 = session['item2']
    item1elo, item2elo = update_elo(item1[3], item2[3])
    for item in items:
        if item == item1:
            item[3] = item1elo
    for item in items:
        if item == item2:
            item[3] = item2elo
    for item in sorted(items, key=itemgetter(3)):
        print(item)
    return redirect("/")

@app.route('/2')
def item_two_wins():
    item1 = session['item1']
    item2 = session['item2']
    item1elo, item2elo = update_elo(item2[3], item1[3])
    for item in items:
        if item == item1:
            item[3] = item1elo
    for item in items:
        if item == item2:
            item[3] = item2elo
    for item in sorted(items[1:], key=itemgetter(3)):
        print(item)
    return redirect("/")


def password_prompt(message):
    return f'''
                <form action="/admin" method='post'>
                  <label for="password">{message}:</label><br>
                  <input type="password" id="password" name="password" value=""><br>
                  <input type="submit" value="Submit">
                </form>'''


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    print(request.method)
    if request.method == 'GET':
        return password_prompt("Admin password:")
    elif request.method == 'POST':
        if request.form['password'] != PASSPHRASE:
            return password_prompt("Invalid password, try again. Admin password:")
        else:
            list_of_products_string = ''
            for item in sorted(items[1:], key=itemgetter(3)):
                list_of_products_string = list_of_products_string + item[0] + '<br>' + str(item[1]) + '<br>' + item[2] + '<br>' + str(item[3]) + '<br>' + '----------' + '<br>'
            return list_of_products_string

if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run()