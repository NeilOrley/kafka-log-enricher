import json
import configparser
from flask import Flask, render_template, request
from confluent_kafka import Consumer, Producer
import atexit

@atexit.register
def shutdown():
    c.close()
    p.flush()



# Lire la configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Configurer le Consumer
consumer_config = {
    'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
    'group.id': config.get('CONSUMER', 'group.id'),
    'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
}

c = Consumer(consumer_config)

# Configurer le Producer
producer_config = {
    'bootstrap.servers': config.get('PRODUCER', 'bootstrap.servers')
}

p = Producer(producer_config)

# Au début, lisez le délai d'attente de la configuration:
MAX_WAIT_TIME = int(config.get('CONSUMER', 'max_wait_time', fallback=10))  # fallback est le délai d'attente par défaut



app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    # Just render the template without fetching any message.
    return render_template('index.html')



@app.route('/get_message', methods=['GET'])
def get_message():
    topic_name = config.get('CONSUMER', 'topic')
    c.subscribe([topic_name])
    elapsed_time = 0

    while elapsed_time < MAX_WAIT_TIME:
        msg = c.poll(1.0)
        if msg:
            return msg.value().decode('utf-8')
        elapsed_time += 1

    return '', 204  # No Content




@app.route('/send', methods=['POST'])
def send():
    log = request.form['log']
    severity = request.form['severity']
    event_type = request.form['event_type']
    enriched_msg = {
        "log": log,
        "severity": severity,
        "event_type": event_type
    }
    output_topic = config.get('PRODUCER', 'output_topic')
    
    # Convert the dictionary to a JSON string
    json_msg = json.dumps(enriched_msg)
    p.produce(output_topic, value=json_msg)
    return "Success", 200

if __name__ == '__main__':
    app.run(debug=True)