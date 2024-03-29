import typing as T

import pytest
from docstring_parser.numpydoc import parse


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None:
    docstring = parse(source)
    assert docstring.short_description == expected
    assert docstring.long_description is None
    assert docstring.meta == []


@pytest.mark.parametrize(
    "source, expected_short_desc, expected_long_desc, expected_blank",
    [
        (
            "Short description\n\nLong description",
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            True,
        ),
        (
            "Short description\nLong description",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description",
            "Long description",
            False,
        ),
        (
            "\nShort description\nLong description\n",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            False,
        ),
    ],
)
def test_long_description(
    source: str,
    expected_short_desc: str,
    expected_long_desc: str,
    expected_blank: bool,
) -> None:
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank
    assert docstring.meta == []


@pytest.mark.parametrize(
    "source, expected_short_desc, expected_long_desc, "
    "expected_blank_short_desc, expected_blank_long_desc",
    [
        (
            """
            Short description
            Parameters
            ----------
            asd
            """,
            "Short description",
            None,
            False,
            False,
        ),
        (
            """
            Short description
            Long description
            Parameters
            ----------
            asd
            """,
            "Short description",
            "Long description",
            False,
            False,
        ),
        (
            """
            Short description
            First line
                Second line
            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            False,
            False,
        ),
        (
            """
            Short description

            First line
                Second line
            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            False,
        ),
        (
            """
            Short description

            First line
                Second line

            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            True,
        ),
        (
            """
            Parameters
            ----------
            asd
            """,
            None,
            None,
            False,
            False,
        ),
    ],
)
def test_meta_newlines(
    source: str,
    expected_short_desc: T.Optional[str],
    expected_long_desc: T.Optional[str],
    expected_blank_short_desc: bool,
    expected_blank_long_desc: bool,
) -> None:
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank_short_desc
    assert docstring.blank_after_long_description == expected_blank_long_desc
    assert len(docstring.meta) == 1


def test_meta_with_multiline_description() -> None:
    docstring = parse(
        """
        Short description

        Parameters
        ----------
        spam
            asd
            1
                2
            3
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].json_desc == "asd\n1\n    2\n3"


def test_default_args():
    docstring = parse(
        """
        A sample function

        A function the demonstrates docstrings

        Parameters
        ----------
        arg1 : int
            The firsty arg
        arg2 : str
            The second arg
        arg3 : float, optional
            The third arg. Default is 1.0.
        arg4 : Optional[Dict[str, Any]], optional
            The fourth arg. Defaults to None
        arg5 : str, optional
            The fifth arg. Default: DEFAULT_ARGS

        Returns
        -------
        Mapping[str, Any]
            The args packed in a mapping
        """
    )
    assert docstring is not None
    assert len(docstring.params) == 5

    arg4 = docstring.params[3]
    assert arg4.arg_name == "arg4"
    assert arg4.is_optional
    assert arg4.type_name == "Optional[Dict[str, Any]]"
    assert arg4.default == "None"
    assert arg4.json_desc == "The fourth arg. Defaults to None"


def test_multiple_meta() -> None:
    docstring = parse(
        """
        Short description

        Parameters
        ----------
        spam
            asd
            1
                2
            3

        Raises
        ------
        bla
            herp
        yay
            derp
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 3
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].json_desc == "asd\n1\n    2\n3"
    assert docstring.meta[1].args == ["raises", "bla"]
    assert docstring.meta[1].type_name == "bla"
    assert docstring.meta[1].json_desc == "herp"
    assert docstring.meta[2].args == ["raises", "yay"]
    assert docstring.meta[2].type_name == "yay"
    assert docstring.meta[2].json_desc == "derp"


def test_params() -> None:
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Parameters
        ----------
        name
            description 1
        priority : int
            description 2
        sender : str, optional
            description 3
        ratio : Optional[float], optional
            description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].json_desc == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].json_desc == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].json_desc == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].json_desc == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Parameters
        ----------
        name
            description 1
            with multi-line text
        priority : int
            description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].json_desc == (
        "description 1\n" "with multi-line text"
    )
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].json_desc == "description 2"


def test_attributes() -> None:
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Attributes
        ----------
        name
            description 1
        priority : int
            description 2
        sender : str, optional
            description 3
        ratio : Optional[float], optional
            description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].json_desc == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].json_desc == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].json_desc == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].json_desc == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Attributes
        ----------
        name
            description 1
            with multi-line text
        priority : int
            description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].json_desc == (
        "description 1\n" "with multi-line text"
    )
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].json_desc == "description 2"


def test_other_params() -> None:
    docstring = parse(
        """
        Short description
        Other Parameters
        ----------------
        only_seldom_used_keywords : type, optional
            Explanation
        common_parameters_listed_above : type, optional
            Explanation
        """
    )
    assert len(docstring.meta) == 2
    assert docstring.meta[0].args == [
        "other_param",
        "only_seldom_used_keywords",
    ]
    assert docstring.meta[0].arg_name == "only_seldom_used_keywords"
    assert docstring.meta[0].type_name == "type"
    assert docstring.meta[0].is_optional
    assert docstring.meta[0].json_desc == "Explanation"

    assert docstring.meta[1].args == [
        "other_param",
        "common_parameters_listed_above",
    ]


def test_yields() -> None:
    docstring = parse(
        """
        Short description
        Yields
        ------
        int
            description
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["yields"]
    assert docstring.meta[0].type_name == "int"
    assert docstring.meta[0].json_desc == "description"
    assert docstring.meta[0].return_name is None
    assert docstring.meta[0].is_generator


def test_returns() -> None:
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None

    docstring = parse(
        """
        Short description
        Returns
        -------
        type
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "type"
    assert docstring.returns.json_desc is None

    docstring = parse(
        """
        Short description
        Returns
        -------
        int
            description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.json_desc == "description"

    docstring = parse(
        """
        Returns
        -------
        Optional[Mapping[str, List[int]]]
            A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "Optional[Mapping[str, List[int]]]"
    assert docstring.returns.json_desc == "A description: with a colon"

    docstring = parse(
        """
        Short description
        Returns
        -------
        int
            description
            with much text

            even some spacing
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.json_desc == (
        "description\n" "with much text\n\n" "even some spacing"
    )


def test_raises() -> None:
    docstring = parse(
        """
        Short description
        """
    )
    assert len(docstring.raises) == 0

    docstring = parse(
        """
        Short description
        Raises
        ------
        ValueError
            description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name == "ValueError"
    assert docstring.raises[0].json_desc == "description"


def test_warns() -> None:
    docstring = parse(
        """
        Short description
        Warns
        -----
        UserWarning
            description
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].type_name == "UserWarning"
    assert docstring.meta[0].json_desc == "description"


def test_simple_sections() -> None:
    docstring = parse(
        """
        Short description

        See Also
        --------
        something : some thing you can also see
        actually, anything can go in this section

        Warnings
        --------
        Here be dragons

        Notes
        -----
        None of this is real

        References
        ----------
        Cite the relevant literature, e.g. [1]_.  You may also cite these
        references in the notes section above.

        .. [1] O. McNoleg, "The integration of GIS, remote sensing,
           expert systems and adaptive co-kriging for environmental habitat
           modelling of the Highland Haggis using object-oriented, fuzzy-logic
           and neural-network techniques," Computers & Geosciences, vol. 22,
           pp. 585-588, 1996.
        """
    )
    assert len(docstring.meta) == 4
    assert docstring.meta[0].args == ["see_also"]
    assert docstring.meta[0].json_desc == (
        "something : some thing you can also see\n"
        "actually, anything can go in this section"
    )

    assert docstring.meta[1].args == ["warnings"]
    assert docstring.meta[1].json_desc == "Here be dragons"

    assert docstring.meta[2].args == ["notes"]
    assert docstring.meta[2].json_desc == "None of this is real"

    assert docstring.meta[3].args == ["references"]


def test_examples() -> None:
    docstring = parse(
        """
        Short description
        Examples
        --------
        long example

        more here
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].json_desc == "long example\n\nmore here"


@pytest.mark.parametrize(
    "source, expected_depr_version, expected_depr_desc",
    [
        (
            "Short description\n\n.. deprecated:: 1.6.0\n    This is busted!",
            "1.6.0",
            "This is busted!",
        ),
        (
            (
                "Short description\n\n"
                ".. deprecated:: 1.6.0\n"
                "    This description has\n"
                "    multiple lines!"
            ),
            "1.6.0",
            "This description has\nmultiple lines!",
        ),
        ("Short description\n\n.. deprecated:: 1.6.0", "1.6.0", None),
        (
            "Short description\n\n.. deprecated::\n    No version!",
            None,
            "No version!",
        ),
    ],
)
def test_deprecation(
    source: str,
    expected_depr_version: T.Optional[str],
    expected_depr_desc: T.Optional[str],
) -> None:
    docstring = parse(source)

    assert docstring.deprecation is not None
    assert docstring.deprecation.version == expected_depr_version
    assert docstring.deprecation.json_desc == expected_depr_desc
