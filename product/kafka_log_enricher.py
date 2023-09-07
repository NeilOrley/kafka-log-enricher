import configparser
from flask import Flask, render_template, request
from confluent_kafka import Consumer, Producer

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


app = Flask(__name__)

@app.route('/')
def index():
    topic_name = config.get('CONSUMER', 'topic')
    c.subscribe([topic_name])
    messages = []
    while len(messages) < 10:  # get 10 messages, adjust as needed
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        messages.append(msg.value().decode('utf-8'))
    return render_template('index.html', messages=messages)

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
    p.produce(output_topic, value=str(enriched_msg))
    return "Success", 200

if __name__ == '__main__':
    app.run(debug=True)