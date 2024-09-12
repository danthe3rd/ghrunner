# GitHub Action Runner - on Slurm

Use resources from Slurm clusters on GH-actions.
How to:
```bash
# Build the runner
(cd src && ./dev.sh build && ./dev.sh layout && ./dev.sh package)
# Build your singularity image in which the workers will run
singularity build --sandbox sandbox/ docker://pytorch/conda-builder:cuda118
cp ./src/Misc/layoutbin/installdependencies.sh sandbox/
singularity run --fakeroot --writable  sandbox/ /installdependencies.sh
# Create a worker - append your favorite slurm options
./create_worker.py RUNNER_TOKEN --gh_label "a100" --gh_url https://github.com/fairinternal/xformers --gres=gpu:1 --partition=a100 --time=3-0
```

# Getting a `RUNNER_TOKEN`

1. Bunnylol `oss YOUR_REPO`
2. Settings
3. Action Runners
4. New Self-Hosted runner