\ProvidesClass{thesis}[]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions

\LoadClass[12pt,oneside]{report}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\RequirePackage{amsmath}
\RequirePackage{geometry}
\RequirePackage{setspace}
\RequirePackage{nomencl}
\RequirePackage{times}
\RequirePackage{url}
\RequirePackage{titlesec}
\RequirePackage{listings}
\RequirePackage{pxfonts}

\RequirePackage{footnote}
\usepackage{setspace}
\usepackage{placeins}
\usepackage{blindtext, graphicx, multirow,latexsym, keyval, ifthen, moreverb}
\usepackage[algochapter]{algorithm2e}
\usepackage{ragged2e}
\usepackage[hidelinks]{hyperref}
\makesavenoteenv{tabular}
\makesavenoteenv{table}
\usepackage{array}
\usepackage{listings}
\lstset{basicstyle=\ttfamily}
\RequirePackage{etoolbox}


% ===============================
% Force full justification everywhere
% ===============================
\AtBeginDocument{%
  \justifying
}

% Re-apply justification after every heading
\pretocmd{\chapter}{\justifying}{}{}
\pretocmd{\section}{\justifying}{}{}
\pretocmd{\subsection}{\justifying}{}{}
\pretocmd{\subsubsection}{\justifying}{}{}


%defining sections and chapters
\titleformat*{\section}{\normalsize\bfseries \slshape}
\titleformat*{\subsection}{\normalsize\bfseries\slshape}
\titleformat*{\subsubsection}{\normalsize\bfseries\slshape}

\titleformat{\chapter}[display]
  {\normalfont\fontsize{18pt}{12pt}\selectfont\bfseries\centering}
  {\MakeUppercase{\chaptertitlename}\ \thechapter}{14pt}{\MakeUppercase}


% Macro for List of Symbols
\def\listofsymbols{\input{symbols} \clearpage}
\def\addsymbol #1: #2#3{$#1$ \> \parbox{5in}{#2 \dotfill \pageref{#3}}\\}
\def\newsymbol#1{\label{#1}}

\pagenumbering{roman}

\setcounter{secnumdepth}{5}
\setcounter{tocdepth}{5}

%header and footer for other pages
%\patchcmd{\chapter}{\thispagestyle{plain}}{\thispagestyle{fancy}}{}

% header and footer of section pages goes here
\pagestyle{fancy}
\fancyhf{}

\lhead{AI-Powered Code Document Generator} %title of the paper goes here
\rhead{}
\fancyfoot{}
\lfoot{{Department of Computer Applications(MCA)}, \textit{GEC Thrissur} }
\rfoot{ \thepage }

% for setting up alternative directory paths to graphics files,
% remember to comment in "graphics" package
%
\graphicspath{{./eps/}{./tiff/}{./jpg/}{./fig/}{./dia/}{./gnuplot/}{./png/}{./images/}}

%renewcommands starts here
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0.5pt}
\renewcommand{\bibname}{BIBLIOGRAPHY}
\renewcommand{\figurename}{Fig.}
\numberwithin{figure}{chapter}
%\renewcommand{\thealgorithm}{\arabic{chapter}.\arabic{algorithm}}
\fancyhfoffset{10pt}
\geometry{verbose,a4paper, lmargin=1.5in,rmargin=1.25in, tmargin=1.0in, bmargin=1.25in} % set margins
\makenomenclature



%Cover page start here

\def\maketitle
{
	\begin{titlepage}
	\thispagestyle{empty}
    \vspace*{1cm}
	\fontsize{16}{16}\selectfont
	\centering{\MakeUppercase{\textbf{AI-POWERED CODE DOCUMENT GENERATOR}}}\\
	\vspace*{2cm}
	\fontsize{12}{12}\selectfont
    \onehalfspacing{ \textit{\centering{Main Project Report submitted in partial fulfillment of the requirements for the award of the degree of
        \textbf{Master of Computer Applications}  of the \textbf{APJ Abdul Kalam Technological University}}}}\\
	\vspace*{1.0cm}
	\centering{\textit{submitted by}} \\
	\vspace*{1cm}
	\fontsize{13}{13}\selectfont
	\noindent{
		\begin{tabular}{p{7cm}cp{5cm}}
		\centering\textbf{ARYA K A} 

		\textbf{(TCR24MCA-2020)} \\
			
		\end{tabular}
	}\\
	\vspace*{2cm}
	{\centering \includegraphics[scale=1]{image/2.jpg}\par}
	\vspace*{0.5cm}
	\centering{\textbf{DEPARTMENT OF COMPUTER APPLICATIONS}}	\\
	\vspace*{0.1cm}
	\centering{\textbf{GOVERNMENT ENGINEERING COLLEGE\\THRISSUR - 680009}}	\\
	\vspace*{0.4cm}	
	\fontsize{12}{13}\selectfont
	\centering{MARCH 2026}	\\
	\pagebreak
	\end{titlepage}
}

% \ProvidesClass{thesis}[]

% \DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
% \ProcessOptions

% \LoadClass[12pt,oneside]{report}
% \RequirePackage{graphicx}
% \RequirePackage{fancyhdr}
% \RequirePackage{amsmath}
% \RequirePackage{geometry}
% \RequirePackage{setspace}
% \RequirePackage{nomencl}
% \RequirePackage{times}
% \RequirePackage{url}
% \RequirePackage{titlesec}
% \RequirePackage{listings}
% \RequirePackage{pxfonts}

% \RequirePackage{footnote}
% \usepackage{setspace}
% \usepackage{placeins}
% \usepackage{blindtext, graphicx, multirow,latexsym, keyval, ifthen, moreverb}
% \usepackage[algochapter]{algorithm2e}
% \usepackage{ragged2e}
% \usepackage[hidelinks]{hyperref}
% \makesavenoteenv{tabular}
% \makesavenoteenv{table}
% \usepackage{listings}
% \usepackage[export]{adjustbox}
% \setkeys{Gin}{width=\linewidth, keepaspectratio}
% \lstset{basicstyle=\ttfamily}


% %defining sections and chapters
% \titleformat*{\section}{\normalsize\bfseries \slshape}
% \titleformat*{\subsection}{\normalsize\bfseries\slshape}
% \titleformat*{\subsubsection}{\normalsize\bfseries\slshape}

% \titleformat{\chapter}[display]
%   {\normalfont\fontsize{18pt}{12pt}\selectfont\bfseries\centering}
%   {\MakeUppercase{\chaptertitlename}\ \thechapter}{14pt}{\MakeUppercase}


% % Macro for List of Symbols
% \def\listofsymbols{\input{symbols} \clearpage}
% \def\addsymbol #1: #2#3{$#1$ \> \parbox{5in}{#2 \dotfill \pageref{#3}}\\}
% \def\newsymbol#1{\label{#1}}

% \pagenumbering{roman}

% \setcounter{secnumdepth}{5}
% \setcounter{tocdepth}{5}

% %header and footer for other pages
% \usepackage{etoolbox}
% %\patchcmd{\chapter}{\thispagestyle{plain}}{\thispagestyle{fancy}}{}

% % header and footer of section pages goes here
% \pagestyle{fancy}
% \fancyhf{}

% \lhead{AI Based Form Filling Assistant Using Document Intelligence} %title of the paper goes here
% \rhead{}
% \fancyfoot{}
% \lfoot{{Department of Computer Applications(MCA)}, \textit{GEC Thrissur} }
% \rfoot{ \thepage }

% % for setting up alternative directory paths to graphics files
% \graphicspath{{./eps/}{./tiff/}{./jpg/}{./fig/}{./dia/}{./gnuplot/}{./png/}{./images/}}

% %renewcommands starts here
% \renewcommand{\headrulewidth}{0.5pt}
% \renewcommand{\footrulewidth}{0.5pt}
% \renewcommand{\bibname}{BIBLIOGRAPHY}
% \renewcommand{\figurename}{Fig.}
% \numberwithin{figure}{chapter}
% %\renewcommand{\thealgorithm}{\arabic{chapter}.\arabic{algorithm}}
% \fancyhfoffset{10pt}
% \geometry{verbose,a4paper, lmargin=1.5in,rmargin=1.25in, tmargin=1.0in, bmargin=1.25in} % set margins
% \makenomenclature



% % ===============================
% % Cover page definition
% % ===============================
% \def\maketitle
% {
% 	\begin{titlepage}
% 	\thispagestyle{empty}
%     \vspace*{1cm}
% 	\fontsize{16}{16}\selectfont
% 	\centering{\MakeUppercase{\textbf{AI BASED FORM FILLING
% ASSISTANT USING DOCUMENT INTELLIGENCE}}}\\
% 	\vspace*{2cm}
% 	\fontsize{12}{12}\selectfont
%     \onehalfspacing{ \textit{\centering{Mini Project Report submitted in partial fulfillment of the requirements for the award of the degree of
%         \textbf{Master of Computer Applications}  of the \textbf{APJ Abdul Kalam Technological University}}}}\\
% 	\vspace*{1.0cm}
% 	\centering{\textit{submitted by}} \\
% 	\vspace*{1cm}
% 	\fontsize{13}{13}\selectfont
% 	\noindent{
% 		\begin{tabular}{p{7cm}cp{5cm}}
% 		\centering\textbf{GOPIKA K} 
% 		\textbf{(TCR24MCA-2033)} \\
			
% 		\end{tabular}
% 	}\\
% 	\vspace*{3cm}
% 	\begin{figure}[ht]
% 	{\centering {\includegraphics[scale=1]{image/2.jpg}}\par}
% 	\end{figure}
% 	\vspace*{0.5cm}
% 	\centering{\textbf{DEPARTMENT OF COMPUTER APPLICATIONS}}	\\
% 	\vspace*{0.1cm}
% 	\centering{\textbf{GOVERNMENT ENGINEERING COLLEGE\\THRISSUR - 680009}}	\\
% 	\vspace*{0.4cm}	
% 	\fontsize{12}{13}\selectfont
% 	\centering{OCTOBER 2025}	\\
% 	\pagebreak
% 	\end{titlepage}
% }


% % ===============================
% % Force full justification globally
% % ===============================
% \RequirePackage{etoolbox}
% \RequirePackage{ragged2e}

% \AtBeginDocument{%
%   \justifying
% }

% % Re-apply justification after headings (fix for centering issues)
% \pretocmd{\chapter}{\justifying}{}{}
% \pretocmd{\section}{\justifying}{}{}
% \pretocmd{\subsection}{\justifying}{}{}
% \pretocmd{\subsubsection}{\justifying}{}{}


% ======================================================
% Final Fix — Force justification inside all environments
% ======================================================

\RequirePackage{etoolbox}
\RequirePackage{ragged2e}

% Make all normal text justified
\AtBeginDocument{\justifying}

% Re-apply after every heading
\pretocmd{\chapter}{\justifying}{}{}
\pretocmd{\section}{\justifying}{}{}
\pretocmd{\subsection}{\justifying}{}{}
\pretocmd{\subsubsection}{\justifying}{}{}

% ============================================================
% FINAL JUSTIFICATION FIX — Make entire thesis perfectly aligned
% ============================================================
\RequirePackage{microtype} % improves word spacing & justification quality

% Force justification inside all common environments
\AtBeginEnvironment{figure}{\centering\justifying}
\AtBeginEnvironment{table}{\centering\justifying}
\AtBeginEnvironment{tabular}{\justifying}
\AtBeginEnvironment{flushleft}{\justifying}
\AtBeginEnvironment{flushright}{\justifying}
\AtBeginEnvironment{center}{\justifying}
\AtBeginEnvironment{quote}{\justifying}
\AtBeginEnvironment{quotation}{\justifying}
\AtBeginEnvironment{itemize}{\justifying}
\AtBeginEnvironment{enumerate}{\justifying}
\AtBeginEnvironment{description}{\justifying}
\AtBeginEnvironment{abstract}{\justifying}
\AtBeginEnvironment{titlepage}{\justifying}
\AtBeginEnvironment{minipage}{\justifying}

% Extra fixes for spacing issues
\setlength{\parindent}{1.5em} % indent paragraphs nicely
\setlength{\parskip}{0pt}     % no extra space between paragraphs
\frenchspacing                % better spacing after periods
\emergencystretch=3em         % prevents overfull lines
