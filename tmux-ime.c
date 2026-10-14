/* See COPYING for permission to use, copy, modify, and distribute this file. */
#include <Carbon/Carbon.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int
print_string(CFStringRef value)
{
	CFIndex size;
	char *buffer;
	int result;

	if (value == NULL)
		return 0;
	size = CFStringGetMaximumSizeForEncoding(CFStringGetLength(value),
	    kCFStringEncodingUTF8) + 1;
	buffer = malloc((size_t)size);
	if (buffer == NULL)
		return 0;
	result = CFStringGetCString(value, buffer, size, kCFStringEncodingUTF8);
	if (result)
		result = fputs(buffer, stdout) != EOF;
	free(buffer);
	return result;
}

static int
current_source(void)
{
	TISInputSourceRef source = TISCopyCurrentKeyboardInputSource();
	int result;

	if (source == NULL) {
		fputs("tmux-ime: cannot read current input source\n", stderr);
		return 1;
	}
	result = print_string(TISGetInputSourceProperty(source,
	    kTISPropertyInputSourceID));
	CFRelease(source);
	if (!result || putchar('\n') == EOF)
		return 1;
	return 0;
}

static CFArrayRef
selectable_sources(void)
{
	const void *keys[] = {
		kTISPropertyInputSourceCategory,
		kTISPropertyInputSourceIsSelectCapable
	};
	const void *values[] = {
		kTISCategoryKeyboardInputSource, kCFBooleanTrue
	};
	CFDictionaryRef filter;
	CFArrayRef sources;

	filter = CFDictionaryCreate(NULL, keys, values, 2,
	    &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);
	if (filter == NULL)
		return NULL;
	sources = TISCreateInputSourceList(filter, false);
	CFRelease(filter);
	return sources;
}

int
main(int argc, char **argv)
{
	CFArrayRef sources;
	CFStringRef requested = NULL;
	TISInputSourceRef source;
	OSStatus status;
	int listing, result = 1;

	if (argc == 1)
		return current_source();
	if (argc != 2 || (argv[1][0] == '-' &&
	    strcmp(argv[1], "--list") != 0)) {
		int help = argc == 2 && strcmp(argv[1], "--help") == 0;
		fputs("Usage: tmux-ime [--list | INPUT_SOURCE_ID]\n"
		    "No argument prints the current input source.\n"
		    "Example: tmux-ime com.apple.keylayout.ABC\n",
		    help ? stdout : stderr);
		return help ? 0 : 2;
	}
	listing = strcmp(argv[1], "--list") == 0;
	if (!listing) {
		requested = CFStringCreateWithCString(NULL, argv[1],
		    kCFStringEncodingUTF8);
		if (requested == NULL) {
			fputs("tmux-ime: invalid UTF-8 input source ID\n", stderr);
			return 2;
		}
	}
	sources = selectable_sources();
	if (sources == NULL) {
		fputs("tmux-ime: cannot enumerate input sources\n", stderr);
		goto done;
	}
	for (CFIndex i = 0; i < CFArrayGetCount(sources); i++) {
		source = (TISInputSourceRef)CFArrayGetValueAtIndex(sources, i);
		CFStringRef id = TISGetInputSourceProperty(source,
		    kTISPropertyInputSourceID);
		if (listing) {
			if (!print_string(id) || putchar('\t') == EOF ||
			    !print_string(TISGetInputSourceProperty(source,
			    kTISPropertyLocalizedName)) || putchar('\n') == EOF)
				goto done;
		} else if (id != NULL && CFEqual(id, requested)) {
			/* Selecting the already-current source is an OS-level no-op. */
			status = TISSelectInputSource(source);
			if (status != noErr)
				fprintf(stderr, "tmux-ime: selection failed (%d)\n",
				    (int)status);
			result = status == noErr ? 0 : 1;
			goto done;
		}
	}
	if (listing)
		result = 0;
	else
		fprintf(stderr, "tmux-ime: enabled input source not found: %s\n",
		    argv[1]);
done:
	if (sources != NULL)
		CFRelease(sources);
	if (requested != NULL)
		CFRelease(requested);
	return result;
}
