uxTools
======================

Plugin that provides a set of Tools for common tasks.


Provides the following features:

* uxTool: list ALL issues.
* uxTool: list MY issues.
* uxTool: create css (for selected class).
* uxTool: paste css object (from webkit inspector).
* uxTool: upload issue ( beta uploading multiple issues from sublime)

Plugin should work in Osx && Win.

Installing
----------

**Without Git:** Download the latest source from [GitHub](https://github.com/gizmo2040/sublime-iTunes-Control/zipball/master) and copy the extracted folder into the Packages directory.

**With Git:** Clone the repository in your Sublime Text 2 Packages directory, located somewhere in user's "Home" directory::

    git clone git://github.com/ergoux/uxTools


The "Packages" packages directory is located at:

* OS X::

    ~/Library/Application Support/Sublime Text 2/Packages/

* Windows::

    %APPDATA%/Sublime Text 2/Packages/

Generating token
----------
Run The folowing command on console, seting your user name.


    curl -u 'YOUR_USER_NAME' -d '{"scopes":["repo"],"note":"uxTools"}' https://api.github.com/authorizations


That should awnser with a object like this one:

    {
      "scopes": [
        "repo"
      ],
      "created_at": "NNNN-NN-NNTnn:nn:nnZ",
      "note": "uxTools",
      "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "updated_at": "NNNN-NN-NNTnn:nn:nnZ",
      "url": "https://api.github.com/authorizations/nnnnnnnn",
      "note_url": null,
      "app": {
        "url": "http://developer.github.com/v3/oauth/#oauth-authorizations-api",
        "name": "uxTools (API)"
      },
      "id": NNNNNN
    }

Copy the token number represented by x's on the example.

On Sublime, open the user settings accesible form the command pallete 'Preferences: Settings - User' or the '⌘ ,' short  cut.

Set the git_token variable,
example:

    {
        "color_scheme": "Packages/Theme - Aqua/Color Schemes/Monokai Aqua.tmTheme",
    	"font_size": NN.0,
    	"git_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    	"ignored_packages":
    	[
    		"Vintage"
    	],
    	"theme": "ProKit.sublime-theme",
    	"todo":
    	{
    		"case_sensitive": true,
    		"patterns":
    		{
    			"BUG": "BUG[\\s]*?:+(?P<bug>.*)$",
    			"NOTE": "NOTE[\\s]*?:+(?P<note>.*)$"
    		},
    		"result_title": "list",
    	}
    }

Save the file, and Thats it.