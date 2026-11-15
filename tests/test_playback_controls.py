import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from ui.playback_controls import SPEEDS, Playback


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_paused_by_default_and_no_time_passes():
    playback = Playback()
    assert playback.paused
    assert playback.sim_dt(0.1) == 0
    assert playback.ticks == 0


def test_play_passes_scaled_time():
    playback = Playback()
    playback.play()
    assert playback.sim_dt(0.1) == pytest.approx(0.1)
    playback.change_speed(1)
    assert playback.sim_dt(0.1) == pytest.approx(0.2)
    assert playback.ticks == 2
    assert playback.sim_time == pytest.approx(0.3)


def test_step_advances_exactly_once_and_stays_paused():
    playback = Playback(step_dt=0.5)
    playback.play()
    playback.step()
    assert playback.paused
    assert playback.sim_dt(0.016) == 0.5
    assert playback.sim_dt(0.016) == 0
    assert playback.ticks == 1


def test_speed_is_clamped():
    playback = Playback()
    for _ in range(10):
        playback.change_speed(1)
    assert playback.speed == SPEEDS[-1]
    for _ in range(10):
        playback.change_speed(-1)
    assert playback.speed == SPEEDS[0]


def test_reset_calls_back_and_clears_counters():
    calls = []
    playback = Playback(on_reset=lambda: calls.append(1))
    playback.play()
    playback.sim_dt(1.0)
    playback.reset()
    assert calls == [1]
    assert playback.paused and playback.ticks == 0 and playback.sim_time == 0


def test_keys_drive_the_controls():
    playback = Playback()
    assert playback.handle_event(key(pygame.K_SPACE))
    assert not playback.paused
    assert playback.handle_event(key(pygame.K_EQUALS))
    assert playback.speed == 2
    assert playback.handle_event(key(pygame.K_n))
    assert playback.paused
    assert not playback.handle_event(key(pygame.K_q))


def test_buttons_can_be_clicked():
    pygame.init()
    surface = pygame.Surface((600, 60))
    playback = Playback()
    playback.draw(surface, surface.get_rect())
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=playback.buttons["play"].center)
    assert playback.handle_event(click)
    assert not playback.paused
    miss = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(599, 59))
    assert not playback.handle_event(miss)
