from __future__ import print_function
import sys
import click
from textx.exceptions import TextXError
from er.visualize import model_export
from er.lang import main


@click.command()
@click.argument('model_file', type=click.Path(exists=True))
@click.option('-d', '--debug', default=False, is_flag=True,
              help='run in debug mode')
def ervis(model_file, debug):
    """
    Converting ER files to dot.
    """

    m = check_load_model(model_file, debug)

    click.echo("Generating '%s.dot' file for model." % model_file)
    click.echo("To convert to PDF run 'dot -Tpdf -O %s.dot'" % model_file)
    model_export(m, "%s.dot" % model_file)


def check_load_model(model, debug=False):
    try:
        metamodel = main()
        print("Meta-model OK.")
    except TextXError as e:
        print("Error in meta-model file.")
        print(e)
        sys.exit(1)

    try:
        model = metamodel.model_from_file(model, debug=debug)
        print("Model OK.")
    except TextXError as e:
        print("Error in model file.")
        print(e)
        sys.exit(1)

    return model
