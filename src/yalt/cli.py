import os
import sys
import json
import argparse

from urllib.parse import quote
from pathlib import Path

import yaml
import webview
from flask import (
    Flask, render_template, request, jsonify, url_for, redirect,
    render_template_string
)


VALID_LABELS = None
BODY = None
DEVELOPMENT = False

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

window = None

app = Flask(
    __name__,
    static_folder=os.path.join(ROOT_DIR, 'static'),
    template_folder=os.path.join(ROOT_DIR, 'templates')
)
sample_list = []
user_name = ""
message = ""

parser = argparse.ArgumentParser()
parser.add_argument("--development", default=False, action="store_true")
parser.add_argument("--user", default="")
args = parser.parse_args()


def get_labels(base_name, remove_others=True):
    path = f"{base_name}.labels"

    if os.path.isfile(path):
        with open(path) as ifile:
            labels = json.load(ifile)

            if remove_others:
                keys = list(labels)
                for k in keys:
                    if k not in VALID_LABELS:
                        del labels[k]

            return labels

    return {}


def save_labels(base_name, labels):
    path = f"{base_name}.labels"

    try:
        with open(path, "w") as ofile:
            json.dump(labels, ofile)

    except:
        pass


def get_sample(base_name):
    path = f"{base_name}.sample"


    with open(path) as ifile:
        return json.load(ifile)


def check_samples_labels():
    for i, (s, _) in enumerate(sample_list):
        sample_list[i] = (s, len(get_labels(s)))


def clean_labels(labels):
    return {
        k: int(v)
        for k, v in labels.items()
        if k in VALID_LABELS and
            VALID_LABELS[k][0] <= int(v) <= VALID_LABELS[k][1]
    }


@app.route("/set_user_name/<user>")
def set_user_name(user):
    global user_name

    if user_name == "":
        with open(".yalt_user", 'w') as ofile:
            print(user, file=ofile)

    user_name = user

    return user_name


@app.route("/logout")
def logout():
    global user_name

    user_name = ""

    if os.path.isfile(".yalt_user"):
        os.remove(".yalt_user")

    return redirect("/")


@app.route("/")
def index():
    sample_list.clear()

    return render_template("index.html", user=user_name)


@app.route("/select-samples")
def select_samples():
    file_types = ('Sample Files (*.sample)', 'All files (*.*)')

    if not DEVELOPMENT:
        result = window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types
        )

    else:
        result = [f"test/{i+1:03d}.sample" for i in range(20)]

    sample_list.clear()

    if result is None:
        return index()

    sample_list.extend((f.replace(".sample", ""), 0) for f in sorted(result))

    return redirect("/list-samples")


@app.route("/label-sample/<int:index>", methods=['GET', 'POST'])
def label_sample(index):
    if index < 0 or index >= len(sample_list):
        return redirect("/list-samples")

    if request.method == "POST":
        base_path = sample_list[index][0]

        sample = get_sample(base_path)
        labels = clean_labels(request.form)

        labels["id"] = sample["id"]
        labels["user"] = user_name

        save_labels(base_path, labels)

        return redirect("/list-samples")

    base_path = sample_list[index][0]
    sample = get_sample(base_path)
    labels = get_labels(base_path)

    body = render_template_string(
        BODY, sample=sample, labels=json.dumps(labels),
        name=os.path.basename(base_path)
    )

    return render_template(
        "label_sample.html", body=body
    )


@app.route("/clear-labels/<int:index>", methods=['GET'])
def clear_labels(index):
    if index < 0 or index >= len(sample_list):
        return redirect("/list-samples")

    if os.path.isfile(f"{sample_list[index][0]}.labels"):
        os.remove(f"{sample_list[index][0]}.labels")

    return redirect("/list-samples")


@app.route("/list-samples")
def list_samples():
    global message

    check_samples_labels()

    m = message

    if len(message) > 0:
        message = ""

    return render_template(
        "sample_list.html",
        samples=[
            (i, os.path.basename(f), c)
            for i, (f,c) in enumerate(sample_list)
        ], user=user_name, message=m
    )


@app.route("/collect-labels")
def collect_labels():
    global message

    parent = Path(sample_list[0][0]).parent
    path = os.path.dirname(sample_list[0][0])

    valid_samples = [
        labels for labels in (
            get_labels(sample[0], remove_others=False)
            for sample in sample_list
        ) if labels is not None and set(labels).issuperset(set(VALID_LABELS))
    ]

    count = len(valid_samples)

    fpath = os.path.join(path, f'{parent}_{user_name}_{count:02d}.jsonl')
    with open(fpath, 'w', encoding="utf-8") as ofile:
        for labels in valid_samples:
            labels["user"] = user_name
            print(json.dumps(labels), file=ofile)

    message = f"{count} samples saved correctly in file: {fpath}"
    message = message.replace("\\", "\\\\")

    return redirect('/list-samples')


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        links.append((rule.endpoint, list(rule.methods)))

    return jsonify(links)


def run():
    global window, VALID_LABELS, BODY, user_name

    if os.path.isfile(".yalt_user"):
        with open(".yalt_user") as ifile:
            user_name = ifile.readline().strip()

    else:
        user_name = args.user

    if not os.path.isfile("./task/validation.yaml"):
        print("./task/validation.yaml not found", file=sys.stderr)
        exit(-1)

    if not os.path.isfile("task/body.html"):
        print("./task/body.html not found", file=sys.stderr)
        exit(-2)

    VALID_LABELS = yaml.load(
        open("./task/validation.yaml", 'r', encoding="utf-8"),
        Loader=yaml.FullLoader
    )

    with open("task/body.html", "r", encoding="utf-8") as ifile:
        BODY = ifile.read()

    if not DEVELOPMENT:
        window = webview.create_window(
            'YALT!: Yet Another Labeling Tool!', app,
            min_size=(1280, 720), maximized=True, zoomable=True,
            text_select=False
        )

        webview.start()

    else:
        app.run(debug=True)


if __name__ == "__main__":
    DEVELOPMENT = args.development
    run()
