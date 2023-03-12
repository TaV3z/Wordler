#!/bin/env python
import json
import time
import subprocess

import click
from lib.connect import invoke


COUNT = 3


def upload_words():
    with open(FILENAME, 'w') as f:
        f.write(json.dumps(WORDS, indent=4))


# TODO:
# - Игнорировать слова с ready = True
def check_time(word):
    current_time = int(time.time())

    if (current_time - WORDS[word]['create']) // 86400 >= 7:
        return True

    return False


def check_anki(word):

    if WORDS[word]['count'] >= COUNT:
        return True


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

    context = " ".join(context) if context else ""

    if word in WORDS.keys():
        WORDS[word]['count'] += 1

        if context:
            WORDS[word]['context'].append(context)

        click.echo(f"Word {color_word} has been updated!")

        # TODO: Этот кусок нужно вызывать здесь и перед увеличением счётчика count. Во втором случае предовращать логику увеличения счётчика. (Можно сделать автоматическое добавление в anki если он запущен, в противном случае отложить до включения (как?))
        if check_anki(word):
            click.echo("This word is ready to memorize.") 

    else: 
        WORDS.update({
                word: {
                    'count': 1,
                    'create': int(time.time()),
                    'context': [context] if context else [],
                }
            }
        )

        click.echo(f"New word {color_word} was add!")

    upload_words()


def output(el, indent):

    if check_anki(el):
        word_status = click.style("anki", fg='blue')
    elif check_time(el):
        word_status = click.style("deprecated", fg='red')
    else: 
        word_status = "in progress"

    word_with_indent = el.ljust(indent)
    word_with_status = f"{word_with_indent} | {word_status}"

    click.echo(word_with_status)


@cli.command()
@click.option('-o', '--order', default='time', type=click.Choice(['alphabet', 'time']))
@click.option('-f', '--fmt', default='names', type=click.Choice(['names', 'all']))
def status(order, fmt):
    try:
        indent = max(map(len, WORDS.keys()))

        if fmt == 'names':
            if order == 'alphabet':
                for el in sorted(list(WORDS.keys())):
                    output(el, indent)
            elif order == 'time':
            # Holy shit
                time_lst = sorted([WORDS[word]['create'] for word in WORDS.keys()])
                for el in time_lst:
                    for word in WORDS.keys():
                        if WORDS[word]['create'] == el:
                            output(word, indent)
                            break
        elif fmt == "all":
            # TODO: 
            # - Жёстко отрефакторить этот кусок и обязательно с flush или аналогом
            print(json.dumps(WORDS, indent=4))
    except Exception as e:
        click.echo(e)
        click.echo("There are no words!")


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


@cli.command()
@click.argument('old_word')
@click.argument('new_word')
def rename(old_word, new_word):
    color_new_word = click.style(f"'{new_word}'", fg='blue')
    color_old_word = click.style(f"'{old_word}'", fg='red')

    try:
        WORDS.update({new_word: WORDS.pop(old_word)})
        upload_words()

        click.echo(f"Word {color_old_word} was removed on {color_new_word}")
    except:
        click.echo(f"There is no {color_old_word} here :(")


# Temporary function. Still alive while anki integration doesn't implement.
@cli.command()
@click.argument('word')
def copy(word):
    color_copy_word = click.style(f"'{word}'", fg='yellow')
    try:
        context = WORDS[word]['context']
        if context:
            cmd = f'echo -n {context[0].strip()} | xclip -selection clipboard'
            subprocess.check_call(cmd, shell=True)

            click.echo(f"Context of {color_copy_word} has been copied.")
        else:
            click.echo(f"{color_copy_word} doesn't have any context.")
    except Exception as e:
        click.echo(f"There is no {color_copy_word} here :(")


@cli.command()
def sync():

    # note = {
    #         'deckName': 'testDeck',
    #         'modelName': 'Basic',
    #         'fields': {
    #             'Front': 'Hey, I\'m front',
    #             'Back': 'Hey, I\'m back',
    #         },
    # }
    # invoke('addNote', note=note)

    ...


if __name__ == '__main__':
    FILENAME = 'test.json'
    try:
        with open(FILENAME) as f:
            WORDS = json.loads(f.read())
    except:
        WORDS = {}

    cli()
