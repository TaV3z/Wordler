#!/bin/env python
import json
import time

import click


def upload_words():
    with open(FILENAME, 'w') as f:
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


def check_all_counts():
    COUNT = 5
    anki_words = []

    for word in WORDS:
        if WORDS[word]['count'] == COUNT:
            anki_words.append(word)

    return "No words to anki" if not anki_words else "\n".join(anki_words)

def check_word_count(word):
    if WORDS[word]['count'] >= 5:
        click.echo("This word is ready to memorize.")

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
        check_word_count(word)
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
    word_with_indent = el.ljust(indent)
    word_status = click.style("anki", fg='blue') if WORDS[el]['count'] >= 5 else "in progress"
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
def rename(word):
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
def mv(old_word, new_word):
    color_new_word = click.style(f"'{new_word}'", fg='blue')
    color_old_word = click.style(f"'{old_word}'", fg='red')
    try:
        WORDS.update({new_word: WORDS.pop(old_word)})
        upload_words()

        click.echo(f"Word {color_old_word} was removed on {color_new_word}")
    except:
        click.echo(f"There is no {color_old_word} here :(")


if __name__ == '__main__':
    FILENAME = 'words.json'
    try:
        with open(FILENAME) as f:
            WORDS = json.loads(f.read())
    except:
        WORDS = {}

    cli()
