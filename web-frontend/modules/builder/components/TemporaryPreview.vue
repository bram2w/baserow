<template>
  <div>
    <div style="padding: 30px">
      <header>
        <nav>
          <p>HEADER</p>
          <menu id="navmenu" type="context">
            <menuitem label="Home" icon="icon.png">
              <a href="#">Home</a>
            </menuitem>
          </menu>
        </nav>
      </header>
    </div>
    <slot></slot>
    <div style="padding: 30px">
      <main>
        <h1>Heading...</h1>
        <h2>Heading...</h2>
        <h3>Heading...</h3>
        <h4>Heading...</h4>
        <h5>Heading...</h5>
        <h6>Heading...</h6>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus
          nisi lacus, auctor sit amet purus vel, gravida luctus lectus. Aenean
          rhoncus dapibus enim, sit amet faucibus leo ornare vitae. <br />
          <span> span </span>
          <b>Bold word</b>
          <i>italic</i>
          <em>emphasis</em>
          <mark>mark</mark>
          <small> small </small>
          <sub> sub </sub>
          <sup> sup </sup>
          <u> Statements... </u>
          <abbr title="National Aeronautics and Space Administration"
            >NASA</abbr
          >
          <strike> strikethrough </strike>
          <span><del> deprecated info </del> <ins> new info </ins> </span>
          <s> not relevant </s>
          <a href="#link">link</a>
          <time datetime="2020-08-17 08:00">Monday at 8:00 AM</time>
          <br />
          <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>CANC</kbd>
        </p>
      </main>

      <p>This is a <q>short quote</q></p>
      <blockquote>
        This instead is a long quote that is going to use a lot of words and
        also cite who said that. —<cite>Some People</cite>
      </blockquote>

      <ol>
        <li><data value="21053">data tag</data></li>
        <li><data value="23452">data tag</data></li>
        <li><data value="42545">data tag</data></li>
        <li>List item</li>
        <li>List item</li>
        <li>List item</li>
      </ol>

      <ul>
        <li>List item</li>
        <li>List item</li>
        <li>List item</li>
        <li>List item</li>
        <li>List item</li>
        <li>List item</li>
      </ul>

      <hr />

      <video
        width="100%"
        height="480"
        style="max-width: 100%"
        src="https://archive.org/download/Popeye_forPresident/Popeye_forPresident_512kb.mp4"
        controls
      >
        <track kind="subtitles" src="subtitles_de.vtt" srclang="de" />
        <track kind="subtitles" src="subtitles_en.vtt" srclang="en" />
        <track kind="subtitles" src="subtitles_ja.vtt" srclang="ja" />
        Sorry, your browser doesn't support HTML5 <code>video</code>, but you
        can download this video from the
        <a
          href="https://archive.org/details/Popeye_forPresident"
          target="_blank"
          >Internet Archive</a
        >.
      </video>

      <object
        data="flashmovie.swf"
        width="600"
        height="800"
        type="application/x-shockwave-flash"
      >
        Please install the Shockwave plugin to watch this movie.
      </object>

      <pre style="max-width: 100%; overflow: scroll">

                                                                               _,'/
                                                                      _.-''._:
                                                      ,-:`-.-'    .:.|
                                                   ;-.''       .::.|
                      _..------.._  / (:.       .:::.|
               ,'.   .. . .  .`/  : :.     .::::.|
           ,'. .    .  .   ./    \ ::. .::::::.|
       ,'. .  .    .   . /      `.,,::::::::.;\
      /  .            . /       ,',';_::::::,:_:
   / . .  .   .      /      ,',','::`--'':;._;
  : .             . /     ,',',':::::::_:'_,'
  |..  .   .   .   /    ,',','::::::_:'_,'
  |.              /,-. /,',':::::_:'_,'
  | ..    .    . /) /-:/,'::::_:',-'
  : . .     .   // / ,'):::_:',' ;
   \ .   .     // /,' /,-.','  ./
      \ . .  `::./,// ,'' ,'   . /
       `. .   . `;;;,/_.'' . . ,'
          ,`. .   :;;' `:.  .  ,'
       /   `-._,'  ..  ` _.-'
      (     _,'``------''
       `--''

      </pre>
      <p>
        <var> variable </var> = 1000;
        <samp
          >Traceback (most recent call last):<br />NameError: name 'variabl' is
          not defined</samp
        >
      </p>
      <table>
        <thead>
          <tr>
            <th>Numbers</th>
            <th>Letters</th>
            <th>Colors</th>
          </tr>
        </thead>
        <tfoot>
          <tr>
            <td>123</td>
            <td>ABC</td>
            <td>RGB</td>
          </tr>
        </tfoot>
        <tbody>
          <tr>
            <td>1</td>
            <td>A</td>
            <td>Red</td>
          </tr>
          <tr>
            <td>2</td>
            <td>B</td>
            <td>Green</td>
          </tr>
          <tr>
            <td>3</td>
            <td>C</td>
            <td>Blue</td>
          </tr>
        </tbody>
      </table>

      <p>
        A <dfn>definition</dfn> is an explanation of the meaning of a word or
        phrase.
      </p>

      <details>
        <summary>Summary of content below</summary>
        <p>Content 1</p>
        <p>Content 2</p>
        <p>Content 3</p>
        <p>Content 4</p>
      </details>
      <section>
        <h1>Content</h1>
        <p>Informations about content.</p>
      </section>

      <progress value="33" max="100"></progress>
      <meter value="11" min="0" max="45" optimum="40">25 out of 45</meter>

      <p>2+2 = <output>4</output></p>

      <select>
        <optgroup label="Choice [1-3]">
          <option value="1">One</option>
          <option value="2">Two</option>
          <option value="3">Three</option>
        </optgroup>
        <optgroup label="Choice [4-6]">
          <option value="4">Four</option>
          <option value="5">Five</option>
          <option value="6">Six</option>
        </optgroup>
      </select>

      <div>
        <div>
          <p>div > div > p</p>
        </div>

        <br />
      </div>
      <svg width="100" height="100">
        <circle
          cx="50"
          cy="50"
          r="40"
          stroke="green"
          stroke-width="4"
          fill="yellow"
        />
      </svg>

      <br />

      <textarea
        id="textarea"
        name="textarea"
        rows="4"
        cols="50"
        style="max-width: 100%"
      >
          Write something in here
      </textarea>

      <br />

      <audio controls>
        I'm sorry. You're browser doesn't support HTML5 <code>audio</code>.
        <source
          src="https://archive.org/download/ReclaimHtml5/ReclaimHtml5.ogg"
          type="audio/ogg"
        />
        <source
          src="https://archive.org/download/ReclaimHtml5/ReclaimHtml5.mp3"
          type="audio/mpeg"
        />
      </audio>
      <p>
        This is a recording of a talk called <cite>Reclaim HTML5</cite> which
        was orinally delieved in Vancouver at a
        <a
          href="http://www.meetup.com/vancouver-javascript-developers/"
          taget="_blank"
          >Super VanJS Meetup</a
        >. It is hosted by
        <a href="https://archive.org/details/ReclaimHtml5" target="_blank"
          >The Internet Archive</a
        >
        and licensed under
        <a
          href="http://creativecommons.org/licenses/by/3.0/legalcode"
          target="_blank"
          >CC 3.0</a
        >.
      </p>

      <iframe
        src="https://open.spotify.com/embed?uri=spotify%3Atrack%3A67HxeUADW4H3ERfaPW59ma?si=PogFcGg9QqapyoPbn2lVOw"
        width="300"
        height="380"
        frameborder="0"
        allowtransparency="true"
      ></iframe>

      <article>
        <header>
          <h2>Title of Article</h2>
          <span>by Arthur T. Writer</span>
        </header>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam
          volutpat sollicitudin nisi, at convallis nunc semper et. Donec
          ultrices odio ac purus facilisis, at mollis urna finibus.
        </p>
        <figure>
          <img
            src="https://placehold.it/600x300"
            alt="placeholder-image"
            style="max-width: 100%"
          />
          <figcaption>Caption.</figcaption>
        </figure>
        <footer>
          <dl>
            <dt>Published</dt>
            <dd>17 August 2020</dd>
            <dt>Tags</dt>
            <dd>Sample Posts, html example</dd>
          </dl>
        </footer>
      </article>

      <form>
        <fieldset>
          <legend>Personal Information</legend>
          <label for="name">Name</label><br />
          <input id="name" name="name" /><br />
          <label for="dob">Date of Birth</label><br />
          <input id="dob" name="dob" type="date" />
        </fieldset>
      </form>

      <aside>
        <p>P inside ASIDE tag</p>
      </aside>
      <map name="shapesmap">
        <area shape="rect" coords="29,32,230,215" href="#square" alt="Square" />
        <area shape="circle" coords="360,130,100" href="#circle" alt="Circle" />
      </map>

      <img
        src="https://placehold.it/100x100"
        alt="placeholder-image"
        style="max-width: 100%"
      />

      <form action="" method="get">
        <label for="browser">Choose your browser from the list:</label>
        <input id="browser" list="browsers" name="browser" />
        <datalist id="browsers">
          <option value="Edge" />
          <option value="Firefox" />
          <option value="Chrome" />
          <option value="Opera" />
          <option value="Safari" />
        </datalist>
        <input type="submit" />
      </form>

      <footer>
        <address>
          relevant contacts <a href="mailto:mail@example.com">mail</a>.
        </address>
        <div>created by <a href="https://blazardsky.space">@blazardsky</a></div>
      </footer>
    </div>
  </div>
</template>
