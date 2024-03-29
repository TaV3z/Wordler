#!/bin/env python
import json
import time
import subprocess

import click
from lib.translate_mod import translate
from lib.connect import invoke


COUNT = 3


def upload_words():
    with open(FILENAME, 'w') as f:
        f.write(json.dumps(WORDS, indent=4))


def check_time(word):
    current_time = int(time.time())

    if (current_time - WORDS[word]['create']) // 86400 >= 7:
        return True

    return False


def check_anki(word):

    if WORDS[word]['count'] >= COUNT:
        return True


@click.group()
def cli():
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
            context_color = click.style(f"\"{WORDS[word]['context']}\"", fg="yellow")
            click.confirm(f"You already have a context of this word:\n\n{context_color}\n\nDo you want to overwrite it? ", abort=True)
            WORDS[word]['context'] = context

        click.echo(f"Word {color_word} has been updated!")

        # TODO: Этот кусок нужно вызывать здесь и перед увеличением счётчика count. Во втором случае предовращать логику увеличения счётчика. (Можно сделать автоматическое добавление в anki если он запущен, в противном случае отложить до включения (как?))
        if check_anki(word):
            click.echo("This word is ready to memorize.") 

    else: 
        WORDS.update({
                word: {
                    'count': 1,
                    'create': int(time.time()),
                    'context': context if context else '',
                }
            }
        )

        click.echo(f"New word {color_word} was add!")

    upload_words()


def output(el, indent):

    if check_anki(el):
        word_status = click.style("anki".ljust(11), fg='blue')
    elif check_time(el):
        word_status = click.style("deprecated".ljust(11), fg='red')
    else: 
        word_status = "in progress"

    word_with_indent = el.ljust(indent)
    word_context = "+".center(7) if WORDS[el]["context"] else "-".center(7)
    word_with_status = f"{word_with_indent} | {word_status} | {word_context}"

    click.echo(word_with_status)


# TODO: 
# - Use error handlers and transport upload_words at the end of if block
@cli.command()
def clear():
    for word in WORDS.copy():
        if check_time(word) and not check_anki(word):
            del WORDS[word]
            word = click.style(word, fg='red')
            click.echo(f"Word {word} deleted because it was deprecated.")

    upload_words()


@cli.command()
@click.option('-f', '--fmt', default='names', type=click.Choice(['names', 'all']))
def status(fmt):
    try:
        indent = max(map(len, WORDS.keys()))
        title = f"{'word'.ljust(indent)} | {'state'.ljust(11)} | context"
        click.echo(title)
        click.echo('-' * len(title))

        if fmt == 'names':
            for el in sorted(list(WORDS.keys())):
                output(el, indent)
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
            cmd = f'echo -n {context.strip()} | xclip -selection clipboard'
            subprocess.check_call(cmd, shell=True)

            click.echo(f"Context of {color_copy_word} has been copied.")
        else:
            click.echo(f"{color_copy_word} doesn't have any context.")
    except Exception as e:
        click.echo(f"There is no {color_copy_word} here :(")


@cli.command
def sync():
    # TODO:
    # All code after this e-handler doesn't wait until it ends
    try:
        invoke('createDeck', deck="Wordler")
    except:
        cmd = f'anki &'
        subprocess.check_call(cmd, shell=True)


    deck = f"Wordler::{time.asctime()}"
    # TODO:
    # There can be an empty deck.
    invoke('createDeck', deck=deck)

    for word in WORDS.copy():
        if check_anki(word):
            transmit_to_anki(word, deck)
            del WORDS[word]

    upload_words()
    click.echo("All words were successfully transmitted.")


def transmit_to_anki(word, deck):
    model = 'English card'
    context = WORDS[word]['context']


    note = {
            'deckName': deck,
            'modelName': model,
            'fields': {
                'Лицо': word,
                'Контекст': context,
                'Оборот': translate(word),
            }
    }

    try: 
        invoke('addNote', note=note)
    except Exception as e:
        print(f"Something goes wrong!\n{e}")


if __name__ == '__main__':
    # FILENAME = 'test.json'
    FILENAME = 'words.json'

    try:
        with open(FILENAME) as f:
            WORDS = json.loads(f.read())
    except:
        WORDS = {}

    cli()
