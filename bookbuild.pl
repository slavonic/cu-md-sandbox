#!/usr/bin/perl

use warnings;
use strict;
use utf8;
use XML::Parser;
use Tie::IxHash;
use File::Basename;

# take a Manifest file and construct the HTML data for a liturgical book
# use the cumd processor as a backend

my $input = $ARGV[0];
die "Manifest file not found" unless (-e $input);

############# BEGIN PARSING SUBS ###############
my %metadata = ();
tie my %chapters, "Tie::IxHash"; # a hash for storing the chapters in sequential order

sub default {
	return;
}

sub text {
	return;
}

sub startElement {
	my( $parseinst, $element, %attrs ) = @_;
	SWITCH: {
		if ($element eq "meta") {
			# this is a meta information tag
			# push its contents into the meta hash
			$metadata{$attrs{name}} = $attrs{content};
			last SWITCH;
		}
		if ($element eq "chapter") {
			# this gives us the chapter name of the appropriate file
			$chapters{$attrs{file}} = $attrs{name};
			last SWITCH;
		}
	};
}

sub endElement {
	my ($parseinst, $elem) = @_;
	return;
}
####### END OF PARSING SUBS #####################

my $outputdir = "/home/sasha/design/ponomar/maktabah";
my $parser = new XML::Parser(ErrorContext => 2);
$parser->setHandlers(	Start   => \&startElement,
			End     => \&endElement,
			Char    => \&text,
			Default => \&default);
$parser->parsefile($input);

# set up parameters
my $title = $metadata{title};
my $path = $metadata{latin} . $metadata{year};
my($filename, $dirs, $suffix) = fileparse($input);

mkdir "$outputdir/$path" || die "Output directory $path already exists!";

# create Index file
open (OUTPUT, ">:encoding(UTF-8)", "$outputdir/$path/index.html") || die "Cannot write to output file: $!";
print OUTPUT qq(<!DOCTYPE html>
<html>
<head>
	<title>$title</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width">
	<link rel="stylesheet" href="https://www.ponomar.net/css/book.css">
</head>
<body>
);

print OUTPUT qq(<p text_align="center">$title</p>\n);
print OUTPUT qq(<p text_align="center">$metadata{publisher}, $metadata{year}</p>\n);
print OUTPUT qq(<p text_align="center">Contents</p>\n);
print OUTPUT qq(<ul>\n);
foreach my $chapter (keys %chapters) {
	print OUTPUT qq(<li><a href="$chapter.html" name="$chapter">$chapters{$chapter}</a></li>\n);
}
print OUTPUT qq(
</ul>
</body>
</html>);
close (OUTPUT);

my $j = 0;
foreach my $chapter (keys %chapters) {
    system ("cumd -e footnotes $dirs/chapters/$chapter.md toomp.html");
    # now create the HTML file
	open (OUTPUT, ">:encoding(UTF-8)", "$outputdir/$path/$chapter.html") || die "Cannot write to output file: $!";
	print OUTPUT qq(<!DOCTYPE html>
<html>
<head>
	<title>$chapters{$chapter}</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width">
    <link rel="stylesheet" href="https://sci.ponomar.net/css/fonts.css">
	<link rel="stylesheet" href="https://www.ponomar.net/css/book.css">
</head>
<body>
);
	# navigation panel
	print OUTPUT qq(
<div class="nav"><table align="center"><tr>);
	print OUTPUT $j == 0 ? qq(<td>&lt;&lt;&nbsp;Previous</td>) : qq(<td><a href=") . (keys(%chapters))[$j - 1] . qq(.html">&lt;&lt;&nbsp;Previous</a></td>);
	print OUTPUT qq(<td><a href="index.html#$chapter">Contents</a></td>);
	print OUTPUT $j == scalar keys(%chapters) ? qq(<td>Next&nbsp;&gt;&gt;</td>) : qq(<td><a href=") . (keys(%chapters))[$j + 1] . qq(.html">Next&nbsp;&gt;&gt;</a></td>);
	print OUTPUT qq(</tr></table></div>\n);
	print OUTPUT qq(<cu>\n);
	# here goes the file
	open (TOOMP, "<:encoding(UTF-8)", "toomp.html") || die "Cannot read from toomp: $!";
	while (<TOOMP>) {
		print OUTPUT $_;
	}
	close (TOOMP);
	unlink "toomp.html";
	# bottom navigation panel
	print OUTPUT qq(
</cu>
<div class="nav"><table align="center"><tr>);
	print OUTPUT $j == 0 ? qq(<td>&lt;&lt;&nbsp;Previous</td>) : qq(<td><a href=") . (keys(%chapters))[$j - 1] . qq(.html">&lt;&lt;&nbsp;Previous</a></td>);
	print OUTPUT qq(<td><a href="index.html#$chapter">Contents</a></td>);
	print OUTPUT $j == scalar keys(%chapters) ? qq(<td>Next&nbsp;&gt;&gt;</td>) : qq(<td><a href=") . (keys(%chapters))[$j + 1] . qq(.html">Next&nbsp;&gt;&gt;</a></td>);
	print OUTPUT qq(</tr></table></div>\n);
	print OUTPUT qq(
</body>
</html>);
	close (OUTPUT);
	$j++;
}
