# Obsidian Setup and Website Editing

![](pictures/Obsidian.png)

## Downloading Obsidian

Download Obsidian from this link [Download - Obsidian](https://obsidian.md/download) 

Open the downloaded exe and go through the installation setup

Utilize all default options, you should just be clicking **next** or **continue** or **install**

## Setting up Obsidian

Once downloaded select the option to open existing folder

![](pictures/obsidianopenfolder.png)


Select the GitHub repo folder you location you had chosen previously in the GitHub setup step [GitHub Setup and Resources — BlueHorizon](https://grantstec.github.io/BlueHorizon-Website/resources/GitHub%20Setup%20and%20Resources.html#github-desktop-setup)

Select and open the **"BlueHorizon-Website"** folder

Select **Trust author and enable plugins**

![](pictures/trustauthorsobsidianopening.png)



## Website Editing

### New Section/Folder

If you would like to make a new section simply hit the create a folder button in upper left

![](pictures/newfolder.png)

This will create an **"Untitled"** folder outside everything

![](pictures/newfolderuntitled.png)

Simple now click and drag this new folder into the location you would like either under the **"docs"** folder for a whole new section like **"subteams"** or **"resources"** or you can place this within a section like **"subteams"** or **"resources"** and it will become a subsection

![](pictures/foldersubsection.png)

Every new subsection should have a **"MAIN"** page that will display when you click on that sections label on the website, for example if you create a new section like engine you now must make a **"MAIN Engine"** file within it, you must include **"MAIN"** or else the auto setup will not detect it, you can have any name after MAIN in the title. Follow the [New Page](#New%20Page) setup to accurately make the new **"MAIN"** page.

![](pictures/MAINfilesetup.png)
### New Page

From here you can now simply navigate the folders and files on the left side of the screen 

![](pictures/Fileandfoldernavigation.png)

The files exist as actual pages, you can simply create a new file by hitting the button with a little pencil in the upper left 

![](pictures/Addnewpage.png)

Once created you will be prompted to give it a name, this is the actual file name, it is not what it will be labeled on website. 

![](pictures/newfilename.png)

The label or title that will appear on website will be following this document title with a new line and then one # and a space then the name. For markdown the common header structure is # for a large header then progressively down to subheading with ##### 

![](pictures/samplepagesetup.png)

### Adding Images

Once of the easiest ways to add images is using the windows inherit snipping tool for screenshots with then get automatically saved to your clipboard so you can just copy paste instead of needing to upload photos and all. I find it so effective I will open regular downloaded images in the windows photo viewer and then just a take a screenshot of that image so I can quickly paste it in a rename name it without need to upload the image in the correct folder and then rename and add the link in the notebook, this can all be done automatically with pasting. 

To activate the snipping tool use **"Win + shift + s"** or search snipping tool in the windows desktop search bar (keyboard shortcut - "Win + s") then select it and I even then right click and add to taskbar so I can simply open it from my taskbar easily. 

![](pictures/snippingtool.png)

### Photo Setup

To ensure effective and efficient copy pasting of images you need to change settings in the obsidian app. 

Navigate to the setting by clicking this gear in bottom left

![](pictures/Obsidian%20Settings.png)

From there adjust your files and links settings so image pasting is correct and efficient

1. Change "Default location for new attachments" to "In subfolder under current folder"
2. Subfolder name become "pictures"
3. New link format should be set to "Path from current file"
4. Ensure "automatically update internal links" is checked
5. Uncheck "use wikilinks"

![](pictures/Pastedimage20260319195313.png)

Now whenever you paste an image into some notebook file it will auto add in a "pictures" folder if it doesn't exist or add the image to the existing pictures folder now you cannot resize the image or else it will not render on the website so unfortunately we are stuck with big images. 

Now you must rename the photo name to remove all spaces or ("%20) to do this it is best to setup the follow plugin [Paste Image Rename Plugin](#Paste%20Image%20Rename%20Plugin)

### Paste Image Rename Plugin

This is a useful plugin to help automatically rename images when you paste them in to prevent any naming errors with spaces in names

Navigate to the settings 

![](pictures/Obsidian%20Settings.png)

Select Community Plugins

![](pictures/PluginInstall.png)

Search for paste image rename

![](pictures/pasteimagerenamesearch.png)
Install it and ensure to click **Enable**

![](pictures/PasteImageRenameenable.png)

Now whenever you paste a screenshot you will be prompted to rename it instantly upon paste

To quickly clear the name box that gets auto filled just hit **"Ctrl + A"** and then begin typing your new name 

Ensure the name does not include any spaces you can use underscores __ to act as spaces

![](pictures/imagerenamepopup.png)

## Quick Tips

### Importing Excels

If you want to import an active excel for people to view data or tables it is fairly easy

They will not be able to edit but can view. 

Ensure to open the excel online on the web browser, the native excel desktop app will not work. 

Click the green **"Share"** button in the upper right and then share again

![](pictures/shareshareexcel.png)

Then select the settings

![](pictures/excelsharesettings.png)

Select **Anyone**,  **Can View** and then **Apply**

![](pictures/excelsharinganyonecanview.png)

Then select **"Copy Link"** 

![](pictures/excelsharingcopylink.png)

now adjust the below line to replace the link with your link

`<iframe` 
  `style="width: 100%; height: 500px; border: none;"` 
  `scrolling="no"` 
  `src="``https://usafa0-my.sharepoint.com/:x:/g/personal/c27grant_stec_afacademy_af_edu/IQD4oKJoUTrcSKvE5nttolIEAVqexKzp3BhkNm7SGdjnUys?e=kiGKpO``&action=embedview&wdAllowInteractivity=True&wdHideHeaders=True&wdDownloadButton=True">`
`</iframe>`

![](pictures/excelsharinglinkadjustment.png)

You can remove the spaces so the final lines look like this 

![](pictures/excelfinalcodelines.png)

Now you will see the excel render in obsidian and the website

<iframe 
  style="width: 100%; height: 500px; border: none;" 
  scrolling="no" 
  src="https://usafa0-my.sharepoint.com/:x:/g/personal/c27grant_stec_afacademy_af_edu/IQD4oKJoUTrcSKvE5nttolIEAVqexKzp3BhkNm7SGdjnUys?e=kiGKpO&action=embedview&wdAllowInteractivity=True&wdHideHeaders=True&wdDownloadButton=True">
</iframe>

![](pictures/excel%20rendered.png)

### Emojis
You can find easy to copy emojis [here](https://getemoji.com/) 

### Tables
Table generator [here](https://www.tablesgenerator.com/markdown_tables).





