#!/usr/bin/python3

import asyncio
import os
import re
from functools import reduce

import aiohttp

from github_stats import Stats


################################################################################
# Helper Functions
################################################################################


def generate_output_folder() -> None:
    """
    Create the output folder if it does not already exist
    """
    if not os.path.isdir("generated"):
        os.mkdir("generated")


################################################################################
# Individual Image Generation Functions
################################################################################


async def get_overview(s: Stats):
    return {
        "name": await s.name,
        "stars": f"{await s.stargazers:,}",
        "forks": f"{await s.forks:,}",
        "contributions": f"{await s.total_contributions:,}",
        "lines_changed": f"{((await s.lines_changed)[0] + (await s.lines_changed)[1]):,}",
        "views": f"{await s.views:,}",
        "repos": f"{len(await s.repos):,}",
    }


async def get_languages(s: Stats):
    top10 = sorted(
        (await s.languages).items(), reverse=True, key=lambda t: t[1].get("size")
    )[:10]

    scale = 100 / reduce(lambda acc,cur: acc + cur[1].get("prop"), top10, 0)
    return top10, scale


def generate_overview(overview, dark=False) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    filename = "overview{}.svg".format("-dark" if dark else "")
    with open(f"templates/{filename}", "r") as f:
        output = f.read()

    output = re.sub("{{ name }}", overview["name"], output)
    output = re.sub("{{ stars }}", overview["stars"], output)
    output = re.sub("{{ forks }}", overview["forks"], output)
    output = re.sub("{{ contributions }}", overview["contributions"], output)
    output = re.sub("{{ lines_changed }}", overview["lines_changed"], output)
    output = re.sub("{{ views }}", overview["views"], output)
    output = re.sub("{{ repos }}", overview["repos"], output)

    generate_output_folder()
    with open(f"generated/{filename}", "w") as f:
        f.write(output)


def generate_languages(top10_languages, percent_scale, dark=False) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    filename = "languages{}.svg".format("-dark" if dark else "")
    with open(f"templates/{filename}", "r") as f:
        output = f.read()

    progress = ""
    lang_list = ""
    for _, (lang, data) in enumerate(top10_languages):
        color = data.get("color")
        color = color if color is not None else "#000000"
        percentage = data.get("prop", 0) * percent_scale
        progress += (
            f'<span style="background-color: {color};'
            f'width: {percentage:0.3f}%;" '
            f'class="progress-item"></span>'
        )
        lang_list += f"""
<li>
    <svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
    viewBox="0 0 16 16" version="1.1" width="16" height="16">
        <circle xmlns="http://www.w3.org/2000/svg" cx="8" cy="9" r="5" />
    </svg>
    <span class="lang">{lang}</span>
    <span class="percent">{percentage:0.2f}%</span>
</li>

"""

    output = re.sub(r"{{ progress }}", progress, output)
    output = re.sub(r"{{ lang_list }}", lang_list, output)

    generate_output_folder()
    with open(f"generated/{filename}", "w") as f:
        f.write(output)


################################################################################
# Main Function
################################################################################


async def main() -> None:
    """
    Generate all badges
    """
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        # access_token = os.getenv("GITHUB_TOKEN")
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    if user is None:
        raise RuntimeError("Environment variable GITHUB_ACTOR must be set.")
    exclude_repos = os.getenv("EXCLUDED")
    excluded_repos = (
        {x.strip() for x in exclude_repos.split(",")} if exclude_repos else None
    )
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    excluded_langs = (
        {x.strip() for x in exclude_langs.split(",")} if exclude_langs else None
    )
    # Convert a truthy value to a Boolean
    raw_ignore_forked_repos = os.getenv("EXCLUDE_FORKED_REPOS")
    ignore_forked_repos = (
        not not raw_ignore_forked_repos
        and raw_ignore_forked_repos.strip().lower() != "false"
    )
    async with aiohttp.ClientSession() as session:
        s = Stats(
            user,
            access_token,
            session,
            exclude_repos=excluded_repos,
            exclude_langs=excluded_langs,
            ignore_forked_repos=ignore_forked_repos,
        )
        overview = await get_overview(s)
        top10_languages, percent_scale = await get_languages(s)
        generate_overview(overview),
        generate_overview(overview, dark=True),
        generate_languages(top10_languages, percent_scale),
        generate_languages(top10_languages, percent_scale, dark=True),


if __name__ == "__main__":
    asyncio.run(main())
