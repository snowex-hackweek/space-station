# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 08:09:07 2021

@author: Beau.Uriona
"""

from dash import html


tidbits = [
    html.Summary("Useful Tidbits"),
    html.P(
        [
            html.Ul(
                [
                    html.Li(
                        "Info",
                        className="my-1",
                    ),
                    html.Ul(
                        [
                            html.Li(
                                "Further info..."
                            ),
                            html.Li("and stuff"),
                            html.Li("even more..."),
                        ],
                        className="my-1",
                    ),
                    html.Li(
                        "Let's summarize here...",
                        className="my-1",
                    ),
                    html.Li(
                        "Author: Beau Uriona, Hydrologist, "
                        "USDA - NRCS, beau.uriona@usda.gov",
                        className="my-1",
                    ),
                ]
            )
        ]
    ),
]


if __name__ == "__main__":
    print("I do nothing, just non dynamic components that take up space...")
