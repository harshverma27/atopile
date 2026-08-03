# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.core.faebrykpy as fbrk
import faebryk.core.node as fabll
import faebryk.library._F as F
from faebryk.libs.net_naming import attach_net_names
from faebryk.libs.nets import bind_electricals_to_fbrk_nets


class _TestPad(fabll.Node):
    is_pad = fabll.Traits.MakeEdge(
        F.Footprints.is_pad.MakeChild(pad_name="TST_PAD", pad_number="1")
    )


def _make_graph():
    g = fabll.graph.GraphView.create()
    tg = fbrk.TypeGraph.create(g=g)
    return g, tg


def _give_pad(g, tg, electrical: F.Electrical) -> None:
    # only electricals reachable from a pad get bound to a net
    lead = fabll.Traits.create_and_add_instance_to(
        node=electrical, trait=F.Lead.is_lead
    )
    pad = _TestPad.bind_typegraph(tg).create_instance(g=g)
    fabll.Traits.create_and_add_instance_to(
        node=lead, trait=F.Lead.has_associated_pads
    ).setup(pad.is_pad.get())


def _net_names(g, tg) -> set[str]:
    nets = bind_electricals_to_fbrk_nets(tg, g)
    attach_net_names(nets)
    return {net.get_name() for net in nets}


def test_power_rail_members_default_net_names():
    g, tg = _make_graph()

    class _App(fabll.Node):
        power = F.ElectricPower.MakeChild()

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)
    _give_pad(g, tg, app.power.get().hv.get())
    _give_pad(g, tg, app.power.get().lv.get())

    assert _net_names(g, tg) == {"hv", "lv"}


def test_override_net_name_on_power_rail_members():
    g, tg = _make_graph()

    class _App(fabll.Node):
        power = F.ElectricPower.MakeChild()
        overrides = [
            fabll.Traits.MakeEdge(
                F.has_net_name_suggestion.MakeChild(
                    name="V3V3", level=F.has_net_name_suggestion.Level.EXPECTED
                ),
                owner=[power, F.ElectricPower.hv],
            ),
            fabll.Traits.MakeEdge(
                F.has_net_name_suggestion.MakeChild(
                    name="GND", level=F.has_net_name_suggestion.Level.EXPECTED
                ),
                owner=[power, F.ElectricPower.lv],
            ),
        ]

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)
    _give_pad(g, tg, app.power.get().hv.get())
    _give_pad(g, tg, app.power.get().lv.get())

    assert _net_names(g, tg) == {"V3V3", "GND"}


def test_override_net_name_on_standalone_electrical():
    g, tg = _make_graph()

    class _App(fabll.Node):
        sig = F.Electrical.MakeChild()
        overrides = [
            fabll.Traits.MakeEdge(
                F.has_net_name_suggestion.MakeChild(
                    name="VDDA_FILT", level=F.has_net_name_suggestion.Level.EXPECTED
                ),
                owner=[sig],
            ),
        ]

    app = _App.bind_typegraph(tg=tg).create_instance(g=g)
    _give_pad(g, tg, app.sig.get())

    assert _net_names(g, tg) == {"VDDA_FILT"}
