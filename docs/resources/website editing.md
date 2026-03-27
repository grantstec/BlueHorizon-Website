# 🌐 Website Editing How-To

## GitHub

```{image} ./pictures/GitHub.png   
:height: 200
:align: center  
``` 

### Setting up GitHub

Navigate to http://github.com and **sign up using your afacademy email**. 

Once you created an account message **Grant Stec** a teams message and he will invite you to the github repo so you can edit. 

On github you can now access the repository called **"BlueHorizon-Website"** found [here](https://github.com/grantstec/BlueHorizon-Website)

```{image} ./pictures/GitHubRepo.png   
:height: 300
:align: center  
``` 
#### Creating your own branch 

Creating your own branch gives you a workspace where you can edit files and push to that branch without crashing the whole website. 

navigate to the tab called **"Branches"** as seen in the picture below
```{image} ./pictures/GitHubRepoBranches.png   
:height: 300
:align: center  
``` 
You should now see the names of the different existing Branches on this repository. 

Name your branch based on **your name**. To make your branch hit the bright green **"New Branch"** button, name it, keep all the other settings that same and hit **"Create New Branch"**. Now you should see your branch listed on the Branches page. 

#### Downloading GitHub Desktop

Download from this link: [Download GitHub Desktop | GitHub Desktop](https://desktop.github.com/download/) 

Open the downloaded exe file and go through the installation setup

It will automatically open the app and then sign in through GitHub.com

##### GitHub Desktop Setup

Use default setup/do not configure manually, just hit finish

![](pictures/ConfigureGit.png)

Clone the repository from the internet

![](pictures/CloneRepo.png)

Search for **"website"** and chose the **BlueHoirzon-Website**. 

![](pictures/WebsiteSearch.png)

If you get a message saying "This folder contains file. Git can only clone to empty folder." You need to choose a folder location locally on your computer, I often just select my **Desktop** or **Documents** 

![](pictures/ChooseFolder.png)

Now you should see a screen like this 

![](pictures/GithubdesktopHomepage.png)
##### GitHub Desktop Branch Selection Setup

Ensure to select your branch from the current branch dropdown 

==**"main" should not be selected ==**

![](pictures/BranchSelection.png)
#### Committing and Pushing Changes

Once you have made edits to the webpage files through [Obsidian](#Obsidian) you need to commit and push your changes to your GitHub Branch

You should see a screen like this in the GitHub Desktop showing the edits and additions you have made 

![](pictures/Githubedits.png)
##### Commit Message

To commit, you must provide a summary in the box highlighted below, you can make it however long or short you like but a quick synopsis like **"added new engine design information"** would work well. There is no need to fill out the description box.

![](pictures/Commitmessage.png)

Once something is typed in you will see the **"Commit _ files to main"** button glow up. Click it. 
##### Pushing

If you made a mistake or want to edit the summary message you can undo the commit by hitting the undo button on the bottom left. 

If all looks good you can push the changes to the actual online repo by hitting **"Push Origin"**

![](pictures/UndoandPush.png)
#### Accessing Your Branch Specific Website

To ensure your edits have been pushed correctly and rendered successfully you can go to your branch specific website. This website will display exactly what is in your branch, it will not be the main website. 

To access it simply adjust the below link to have your branches name in place of the



![](pictures/Pastedimage20260319195313.png)

## Obsidian

![](pictures/ObsidianLogo.png)

### Setting up Obsidian



#### Create Folder

Now create a folder to have the Website files on your computer, this can be made anywhere, Onedrive folders etc. Now once that folder is created go back to VSCode if you have a current folder open go to file and new windows or simple click open folder on the main page and navigate to open the folder you just made. 

```{image} ./pictures/Open_Folder.png  
:height: 300
:align: center  
```
#### Terminal

Now on the bottom of VSCode if there is not a terminal window similar to the one in the bottom of the picture then you would want to move your mouse to the bottom of the window as seen in the next picture and once your courser turns into the double vertical arrows click and drag up this will open the terminal or you can use the hotkey of Ctrl+` (Not apostrophe, button below esc usually).

```{image} ./pictures/vsc_terminal.png  
:height: 300
:align: center  
```

```{image} ./pictures/Terminal_Open.png  
:height: 300
:align: center  
```

Make sure the command line in the terminal windows looks like the folder location you have created and has the same name at the end of the printed line in terminal. Navigate back to the VSC terminal with your folder in the directory and copy this command `git clone https://github.com/grantstec/BlueHorizon-Website.git` and hit enter. 


Once the git clone has finished you should now see your folder populated with all the same files from github. Now you can begin editing and or adding the files. Familiarize yourself with the file structure snd files like intro.md, _config.yml and _toc.yml to learn more about how this file structure works and some niche formatting as seen in intro.md you can visit [Built with Jupyter Book](https://jupyterbook.org/en/stable/intro.html)

### Committing and Pushing

#### Branch Selection

```{warning} 
Do not select "main" branch at any time!
```

Once you are ready to commit and push a new change there are a few things we must make sure as to not destroy the live functioning website running from GitHub. Navigate to the source control tab on the left hand bar above the extensions and above the debugger as seen in the photo. 

```{image} ./pictures/Source_Control.png  
:height: 300
:align: center  
```

You will want to get very familiar with this tab as this is where our version control will be based from and allows us to keep a functioning website running whilst having multiple people edit separate files. If you have made any changes you will see the **Commit** button in blue. We will worry about this later. Most importantly we have to go back to some things we discussed in the beginning of this page and make sure we are pushing to the branch you made. Click on this. 

```{image} ./pictures/branch.png  
:height: 300
:align: center  
```

This will open up a window at the top 

```{image} ./pictures/branch_selection.png  
:height: 300
:align: center  
```

Select your corresponding branch, do the same process of clicking on the branch icon on the bottom Source control tab and selecting you branch.

```{image} ./pictures/Source_Control_Branch.png  
:height: 300
:align: center  
```
Now you should be all set to begin editing the files and once you have made good progress on some edits and or are done for the day it is always a good thing to push to GitHub. 

#### Committing

Once you have made edits go back to the Source Control Tab (Branch looking thing), often below the magnifying glass on the left side bar. In this tab the **"Commit"** button should now be blue with the files you have changes listed below in the "Changes in the Message block type a simple message that relates to what you changed. For example if I added an image called rocket I could say "added rocket image". 

```{image} ./pictures/Commit.png  
:height: 300
:align: center  
```
#### Sync Changes

After you hit commit the button should now change to say **"Sync Change"** Click this button to sync the changes you made. This just double checks that your files are up to date with what you just pushed. If a windows shows up asking **"This action will push and pull commits from and to (Your branch)"**. Just hit **Okay**.

```{image} ./pictures/sync.png  
:height: 200
:align: center  
```
You will want to repeat this process whenever you make any changes.
 

```{note} 
Check your branch has been committed by going back to the repository https://github.com/grantstec/BlueHorizon-Website/branches. In your branch's row there should be a column titled "Updated" confirm the timestamp looks reasonable based on when you last committed and synced.

```

### Changing Main Page

Once you commit ahead of main branch and push to your own branch I will get a message that the branch has been changed and I can move it to main if you are ready for your page to be on home page. Message Grant Stec on Teams.  

### Quick Tips

#### Spell Checker Extension

As you may recall we installed a Spell Checker extension. Whenever you are editing a Markdown file and come across a misspelling a word it will be underlined with a blue squiggly. You can correct these in two ways. The slow way is right click on the word and then go to **"Spelling Suggestions"**, a tab on the top should open with suggested words. The quick way is open the terminal at the bottom and go to the tab called **"SPELL CHECKER"** find a word and double click and you will be directed to it and given options for suggested words and select which ever is correct. You can also add niche words like names to the dictionary so they are ignored by double clicking the word and then click the little diction on the right side of the column. 

```{image} ./pictures/spellchecker.png  
:height: 300
:align: center  
```

#### Markdown Page Viewier

```{warning} 
You must have **Markdown All in One** Extension installed
```

Use "Ctrl" + "Shift" + "V" to get another tab to open in VS Code that shows a preview of the Markdown page. 

#### Emojis
You can find easy to copy emojis [here](https://getemoji.com/) 

#### Tables
Table generator [here](https://www.tablesgenerator.com/markdown_tables).

#### Example Repositories/Websites

Use these examples website to find neat features you may like/want to add and then find them in the code of the repository. You can also learn more about jupyterbook websites as whole from the main documentation website: https://jupyterbook.org/en/stable/intro.html.

##### ECE 281 Website
Website: https://usafa-ece.github.io/ece281-book/intro.html
GitHub: https://github.com/usafa-ece/ece281-book

##### ECE 387 Website 

Website: https://stanbaek.github.io/ece387/intro.html
GitHub: https://github.com/stanbaek/ece387




