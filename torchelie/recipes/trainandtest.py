import copy

import torch

import torchelie.metrics.callbacks as tcb
from torchelie.recipes.recipebase import DataModelLoop, DataLoop

class TrainAndTest:
    """
    Training loop, calls `model.after_train()` after every `test_every`
    iterations. Displays Loss.

    It logs the same things as TrainAndCallBase, plus whatever is returned by
    `model.after_train()`

    Args:
        model (nn.Model): a model
            The model must define:
                - `model.make_optimizer()`
                - `model.after_train()` returns a dict
                - `model.train_step(batch, opt)` returns a dict with key loss
        train_loader (DataLoader): Training set dataloader
        visdom_env (str): name of the visdom environment to use, or None for
            not using Visdom (default: None)
        test_every (int): testing frequency, in number of iterations (default:
            1000)
        train_callbacks (list of Callback): additional training callbacks
            (default: [])
        test_callbacks (list of Callback): additional testing callbacks
            (default: [])
        device: a torch device (default: 'cpu')
    """

    def __init__(self,
                 model,
                 train_fun,
                 test_fun,
                 train_loader,
                 test_loader,
                 test_every=100,
                 visdom_env='main',
                 log_every=10,
                 device='cpu'):

        def eval_call(batch):
            model.eval()
            with torch.no_grad():
                out = test_fun(batch)
            model.train()
            return out

        train_loop = DataModelLoop(model, train_fun, train_loader, device=device)
        test_loop = DataLoop(eval_call, test_loader, device=device)

        train_loop.add_prologues([tcb.Counter()])
        train_loop.add_epilogues([
            tcb.CallDataLoop(test_loop, model, test_every),
            tcb.VisdomLogger(visdom_env=visdom_env, log_every=log_every),
            tcb.StdoutLogger(log_every=log_every),
        ])

        test_loop.add_epilogues([
            tcb.VisdomLogger(
                visdom_env=visdom_env, log_every=-1, prefix='test_'),
            tcb.StdoutLogger(log_every=-1, prefix='Test'),
            tcb.Checkpoint((visdom_env or 'model') + '/ckpt', train_loop)
        ])

        self.train_loop = train_loop
        self.test_loop = test_loop

    def add_callbacks(self, cbs):
        self.train_loop.add_callbacks(cbs)

    def add_test_callbacks(self, cbs):
        self.test_loop.add_callbacks(cbs)

    def fit(self, iters):
        """
        Runs the recipe.

        Args:
            epochs (int): number of epochs

        Returns:
            trained model, test metrics
        """
        return self.train_loop.run(iters)
