# git feature-base

The is a tool that fits in the workflow of creating feature branches. It lists the direct related commits of a given range of commits.

## Usage

1. Go the master branch.

```
git checkout master
```

2. Do some work, then

```
git commit -am 'Part 1 of feature foo'
# Returns commit a12345
```

And then some additional related work maybe

```
git commit -am 'Part 2 of feature foo'
# Returns commit b12345
```

3. Now let's create a feature branch for feature foo. In order to make this feature branch able to be merged into other release branches that are maybe older than `master`, we need to choose an old enough fork point. But if the fork point is too much old, then the feature A wouldn't be able to be applied. So let's use the tool to find this point.

```
git feature-base a12345^
```

or

```
git feature-base a12345^ b12345
```

The tool will give an oldest apply-able commit. Say it’s z98765.

4. Now we create this feature branch with the fork point we just found.

```
git checkout -b feature-foo z98765
git cherry-pick a12345 b12345
```

And then the feature branch is ready.
