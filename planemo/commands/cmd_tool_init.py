"""Module describing the planemo ``tool_init`` command."""

import click

from planemo import io
from planemo import options
from planemo import tool_builder
from planemo.cli import command_function


# --input_format
# --output_format
# --advanced_options
@click.command("tool_init")
@options.tool_init_id_option()
@options.force_option(what="tool")
@options.tool_init_tool_option()
@options.tool_init_name_option()
@options.tool_init_version_option()
@options.tool_init_description_option()
@options.tool_init_command_option()
@click.option(
    "--example_command",
    type=click.STRING,
    default=None,
    prompt=False,
    help=("Example to command with paths to build Cheetah template from "
          "(e.g. 'seqtk seq -a 2.fastq > 2.fasta'). Option cannot be used "
          "with --command, should be used --example_input and "
          "--example_output."),
)
@click.option(
    "--example_input",
    type=click.STRING,
    default=None,
    prompt=False,
    multiple=True,
    help=("For use with --example_command, replace input file (e.g. 2.fastq "
          "with a data input parameter)."),
)
@click.option(
    "--example_output",
    type=click.STRING,
    default=None,
    prompt=False,
    multiple=True,
    help=("For use with --example_command, replace input file (e.g. 2.fastq "
          "with a tool output)."),
)
@click.option(
    "--version_command",
    type=click.STRING,
    default=None,
    prompt=False,
    help="Command to print version (e.g. 'seqtk --version')",
)
@click.option(
    "--named_output",
    type=click.STRING,
    multiple=True,
    default=None,
    prompt=False,
    help=("Create a named output for use with command block for example "
          "specify --named_output=output1.bam and then use '-o $output1' "
          "in your command block."),
)
@click.option(
    "--requirement",
    type=click.STRING,
    default=None,
    multiple=True,
    prompt=False,
    help="Add a tool requirement package (e.g. 'seqtk' or 'seqtk@1.68')."
)
@click.option(
    "--container",
    type=click.STRING,
    default=None,
    multiple=True,
    prompt=False,
    help="Add a Docker image identifier for this tool."
)
@options.tool_init_input_option()
@options.tool_init_output_option()
@options.tool_init_help_text_option()
@options.tool_init_help_from_command_option()
@options.tool_init_doi_option()
@options.tool_init_cite_url_option()
@options.tool_init_test_case_option()
@options.tool_init_macros_option()
@options.build_cwl_option()
@command_function
def cli(ctx, **kwds):
    """Generate tool outline from given arguments."""
    invalid = _validate_kwds(kwds)
    if invalid:
        ctx.exit(invalid)
    tool_description = tool_builder.build(**kwds)
    tool_builder.write_tool_description(
        ctx, tool_description, **kwds
    )


def _validate_kwds(kwds):
    def not_exclusive(x, y):
        if kwds.get(x) and kwds.get(y):
            io.error("Can only specify one of --%s and --%s" % (x, y))
            return True

    def not_specifing_dependent_option(x, y):
        if kwds.get(x) and not kwds.get(y):
            template = "Can only use the --%s option if also specifying --%s"
            message = template % (x, y)
            io.error(message)
            return True

    if not_exclusive("help_text", "help_from_command"):
        return 1
    if not_exclusive("command", "example_command"):
        return 1
    if not_specifing_dependent_option("example_input", "example_command"):
        return 1
    if not_specifing_dependent_option("example_output", "example_command"):
        return 1
    if not_specifing_dependent_option("test_case", "example_command"):
        return 1
    return 0
