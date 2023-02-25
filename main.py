#!/bin/env python
import json
import time

import click


def upload_words():
    with open("words.json", 'w') as f:
        f.write(json.dumps(WORDS, indent=4))


# TODO:
# - Игнорировать слова с ready = True
def check_time():
    current_time = int(time.time())
    outdated_words = []

    for word in WORDS:
        if (current_time - WORDS[word]['create']) // 86400 >= 7:
            outdated_words.append(word)

    return "No words to delete" if not outdated_words else "\n".join(outdated_words)


def check_count():
    COUNT = 5
    anki_words = []

    for word in WORDS:
        if WORDS[word]['count'] == COUNT:
            anki_words.append(word)

    return "No words to anki" if not anki_words else "\n".join(anki_words)


@click.group()
# @click.option('-l', '--lst', default='name', type=click.Choice(['name', 'time']))
# @click.option('-a', '--add')
def cli():
    # click.echo(check_time())
    # click.echo(check_count())
    pass


@cli.command()
@click.argument('word')
@click.argument('context', nargs=-1, required=False)
# @click.option('-c', '--con', default='')
def add(word, context=""):
    word = word.lower()
    color_word = click.style(f"'{word}'", fg='blue')

    if word in WORDS.keys():
        WORDS[word]['count'] += 1

        click.echo(f"Word {color_word} has been updated!")
    else: 
        context = [" ".join(context)] if context else []

        WORDS.update({
                word: {
                    'count': 1,
                    'create': int(time.time()),
                    'context': context,
                }
            }
        )

        click.echo(f"New word {color_word} was add!")

    upload_words()


@cli.command()
@click.option('-o', '--order', default='alphabet', type=click.Choice(['alphabet', 'time']))
@click.option('-f', '--fmt', default='names', type=click.Choice(['names', 'all']))
def status(order, fmt):
    if order == 'alphabet' and fmt == 'names':
        indent = max(map(len, WORDS.keys()))
        for el in sorted(list(WORDS.keys())):
            word_with_indent = el.ljust(indent)
            word_status = click.style("anki", fg='blue') if WORDS[el]['count'] >= 5 else "in progress"
            word_with_status = f"{word_with_indent} | {word_status}"
            click.echo(word_with_status)
    elif fmt == "all":
        # TODO: 
        # - Жёстко отрефакторить этот кусок и обязательно с flush или аналогом
        print(json.dumps(WORDS, indent=4))


@cli.command()
@click.argument('word')
def rm(word):
    color_word = click.style(f"'{word}'", fg='red')
    try:
        del WORDS[word]
        upload_words()
        click.echo(f"Word {color_word} has been removed!")
    except:
        click.echo(f"There is no {color_word} here :(")



if __name__ == '__main__':
    try:
        with open("words.json") as f:
            WORDS = json.loads(f.read())
    except:
        WORDS = {}

    cli()
