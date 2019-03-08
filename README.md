#DDDC Petition Chainspace

Be sure to clone this repo with `--recursive` as it has [submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) in it!

This *should* set everything up for you. It needs to create a symbolic link to your contracts dir at `/app/contracts` which will require sudo

```bash
./init.sh
```

This will run the script `run_end_to_end_petition.py` 

```bash
./run.sh
```

The last thing you should see at the end is:

```bash
14-CITIZEN-count-petition.zencode:
{
    "result": 1,
    "uid": "petition"
}
```

If you see that, everything is working!
