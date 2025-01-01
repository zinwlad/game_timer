import unittest
from unittest.mock import MagicMock
from game_blocker import GameBlocker
import tkinter as tk

class TestGameBlocker(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.blocker = GameBlocker(self.root, ["game.exe", "minecraft.exe"])

    def test_is_game_running(self):
        self.blocker.is_game_running = MagicMock(return_value=True)
        self.assertTrue(self.blocker.is_game_running())

    def test_show_notification(self):
        self.blocker.show_notification = MagicMock()
        self.blocker.show_notification()
        self.blocker.show_notification.assert_called_once()

    def test_block_game(self):
        self.blocker.block_game = MagicMock()
        self.blocker.block_game()
        self.blocker.block_game.assert_called_once()

    def test_final_check_blocks_game(self):
        self.blocker.is_game_running = MagicMock(return_value=True)
        self.blocker.block_game = MagicMock()
        self.blocker.final_check()
        self.blocker.block_game.assert_called_once()

    def test_final_check_no_block_when_game_closed(self):
        self.blocker.is_game_running = MagicMock(return_value=False)
        self.blocker.block_game = MagicMock()
        self.blocker.final_check()
        self.blocker.block_game.assert_not_called()

    def test_monitor_games(self):
        self.blocker.is_game_running = MagicMock(side_effect=[True, False])
        self.blocker.show_notification = MagicMock()
        self.blocker.block_game = MagicMock()
        self.blocker.monitor_games()
        self.blocker.show_notification.assert_called_once()
        self.blocker.block_game.assert_not_called()

    def test_block_game_triggered(self):
        self.blocker.is_game_running = MagicMock(return_value=True)
        self.blocker.show_notification = MagicMock()
        self.blocker.block_game = MagicMock()
        self.blocker.final_check()
        self.blocker.block_game.assert_called_once()

    def test_monitor_games_notification_triggered(self):
        self.blocker.is_game_running = MagicMock(side_effect=[True, False])
        self.blocker.show_notification = MagicMock()
        self.blocker.block_game = MagicMock()
        self.blocker.monitor_games()
        self.blocker.show_notification.assert_called_once()

    def test_monitor_games_block_game_triggered(self):
        self.blocker.is_game_running = MagicMock(side_effect=[True, True])
        self.blocker.show_notification = MagicMock()
        self.blocker.block_game = MagicMock()
        self.blocker.monitor_games()
        self.blocker.block_game.assert_called_once()

if __name__ == '__main__':
    unittest.main()
