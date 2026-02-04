"""Tests for material creation functions."""

from __future__ import annotations

from pyg4ometry import geant4

from pygeomhades.materials import (
    create_aluminum_alloy_material,
    create_aluminum_material,
    create_hd1000_material,
)


def test_create_hd1000_material():
    """Test that create_hd1000_material returns a valid material."""
    reg = geant4.Registry()
    material = create_hd1000_material(reg)

    assert isinstance(material, geant4.Material)
    assert material.name == "HD1000"
    assert material.density == 0.93


def test_create_aluminum_alloy_material():
    """Test that create_aluminum_alloy_material returns a valid material."""
    reg = geant4.Registry()
    material = create_aluminum_alloy_material(reg)

    assert isinstance(material, geant4.Material)
    assert material.name == "EN_AW-2011T8"
    assert material.density == 2.84


def test_create_aluminum_material():
    """Test that create_aluminum_material returns a valid material."""
    reg = geant4.Registry()
    material = create_aluminum_material(reg)

    assert isinstance(material, geant4.Material)
    assert material.name == "Al"
    assert material.density == 2.7
