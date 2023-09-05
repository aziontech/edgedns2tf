FROM hashicorp/terraform:1.5

RUN apk add gcc build-base libffi-dev python3 py3-pip python3-dev

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "idns2tf.py" ]
