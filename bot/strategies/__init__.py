import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.strategies.martingale_strategy import MartingaleStrategy
from bot.strategies.tit_for_tat import TitForTat
from bot.strategies.sma_cross_over import SMACrossOver
from bot.strategies.random_strategy import RandomStrategy
from loss_lurker import LossLurker
from bot.strategies.super_loss_lurker import SuperLossLurker
from bot.strategies.double_loss_lurker import DoubleLossLurker
from bot.strategies.triple_loss_lurker import TripleLossLurker
from bot.strategies.tenth_loss_lurker import TenthLossLurker
from markov_ngram_strategy import MarkovNgramStrategy