# -*- coding: utf-8 -*-
from textx.export import dot_escape
import codecs
import sys
if sys.version < '3':
    text = unicode
else:
    text = str


HEADER = '''
    digraph xtext {
    fontname = "Bitstream Vera Sans"
    fontsize = 8
    node[
        shape=record,
        style=filled,
        fillcolor=aliceblue
    ]
    nodesep = 0.3
    edge[dir=black,arrowtail=empty]


'''


def model_export(model, file_name):
    """
    Exports ER model to dot file.
    """

    processed_set = set()

    with codecs.open(file_name, 'w', encoding="utf-8") as f:
        f.write(HEADER)

        def _export_attr(attr):
            """
            Exports ER attribute.
            """

            # If this is reference do not render as it will be represented
            # as link.
            attr_type = attr.type.type
            if attr_type.__class__.__name__ == 'Entity':
                return ""

            res = "{}{}{}: {}".format(
                "#" if attr.id else "",
                attr.name,
                " '{}'".format(dot_escape(attr.label)) if attr.label else "",
                attr.type.type.name)

            if attr.type.precision_x:
                px = attr.type.precision_x
                py = attr.type.precision_y
                res += "({}{})".format(px, ",{}".format(py) if py else "")

            res += _export_multiplicity(attr.multiplicity)

            res += "\\l"

            return res

        def _export_multiplicity(m):
            if m.upper == m.lower == 1:
                return ""
            else:
                return " [{}{}] ".format(m.lower,
                                         ",{}".format(m.upper)
                                         if m.upper else "")

        def _export_compartment(comp):
            res = "|-[ {} ]-\\l".format(comp.label)
            for attr in comp.attributes:
                res += _export_attr(attr)
            return res

        def _export_enum(enum):
            res = "Enum {}{}|".format(enum.name,
                                      "\\n'{}'".format(enum.label)
                                      if enum.label else "")
            for lit in enum.literals:
                res += "{}: '{}' '{}'\\l".format(lit.name, lit.code, lit.label)
            return res

        def _export_element(elem):
            if elem in processed_set:
                return
            color = ""
            res = ""
            elem_type = elem.__class__.__name__
            if elem_type == 'Entity':
                res += "{}: Entity".format(elem.name)
                if elem.label:
                    res += "\\n'{}'".format(elem.label)
                res += "|"
                # Free attributes
                for attr in elem.attributes:
                    res += _export_attr(attr)
                # compartments
                for comp in elem.compartments:
                    res += _export_compartment(comp)

                # If at least 2 id attributes are entities than this is a
                # "connection" entity.
                c = 0
                for attr in elem.all_attributes:
                    if attr.id:
                        if attr.type.type.__class__.__name__ == 'Entity':
                            c += 1
                else:
                    if c >= 2:
                        color = " fillcolor=coral"

            elif elem_type == 'Enum':
                res += _export_enum(elem)
                color = " fillcolor=wheat"

            res = "{}[label=\"{{{}}}\"{}]\n".format(id(elem), res, color)

            f.write(res)

            # Entity references
            def _render_ref(attr):
                target = attr.type.type
                if target.__class__.__name__ == 'Entity':
                    # If attr is a reference
                    mult = _export_multiplicity(attr.multiplicity)
                    f.write("{} -> {} [label=\"{}{}\"{}{}]\n"
                            .format(id(elem), id(target),
                                    "#" if attr.id else "",
                                    attr.name,
                                    " headlabel=\"{}\"".format(mult)
                                    if mult else "",
                                    " arrowtail=diamond dir=both"
                                    if attr.ref and
                                    attr.ref.containment else ""))

            if elem_type == 'Entity':
                for attr in elem.attributes:
                    _render_ref(attr)
                for comp in elem.compartments:
                    for attr in comp.attributes:
                        _render_ref(attr)

        for element in model.elements:
            _export_element(element)

        f.write('\n}\n')
