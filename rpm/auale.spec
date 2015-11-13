Name:           auale
Version:        1.1.0
Release:        2
Summary:        A free mancala game for the serious player
URL:            http://www.joansala.com/auale
Source0:        http://www.joansala.com/auale/packages/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%if %{defined suse_version}
License:        GPL-3.0+
%else
License:        GPLv3+
%endif

%if %{defined mgaversion}
Group:          Games/Boards
%else
Group:          Amusements/Games
%endif

BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python >= 2.6
Requires:       gtk3 >= 3.10
Requires:       jre >= 1.6
Requires:       desktop-file-utils

%if %{defined fedora}
Requires:       pygobject3 >= 3.8
Requires:       pycairo
%endif

%if 0%{?fedora_version} >= 21
Requires:       SDL2
Requires:       SDL2_mixer
%endif

%if %{defined suse_version}
Requires:       python-gobject >= 3.8
Requires:       python-gobject-cairo >= 3.8
Requires:       python-cairo
Requires:       typelib-1_0-Gtk-3_0
Requires:       typelib-1_0-Rsvg-2_0
Requires:       glib2-tools
%endif

%if 0%{?suse_version} > 1000
Requires:       SDL2
Requires:       SDL2_mixer
%endif

%if %{defined mgaversion}
Requires:       python-cairo
Requires:       python-gi
Requires:       python-gi-cairo
Recommends:     %{_lib}sdl2_mixer2.0_0
%else
%define         _gamesbindir    %{_bindir}
%define         _gamesdatadir   %{_datadir}
%define         _iconsdir       %{_datadir}/icons
%endif

%description
Aualé is a graphical user interface for the popular Oware Abapa board
game. It may be used to analyze, record and share your own mancala
games or to play against the computer.

This interface communicates with an oware engine through an adapted
version of the Universal Chess Interface protocol, which makes it
suitable for use with multiple mancala playing programs. Although,
currently only the Aalina game engine supports this protocol.

Some of its main features include:

 * Play against the computer or watch how it plays.
 * Easily configurable computer strength.
 * Annotate your matches with an easy to use interface.
 * Save your games using a portable format which resembles that of
   the popular Portable Game Notation format.

%prep
%setup -q

%build
pushd %{_builddir}/%{name}-%{version}/src/%{name}
%{__python} setup.py build
popd

%install
pushd %{_builddir}/%{name}-%{version}/src/%{name}
%{__python} setup.py install \
    --root=%{buildroot} \
    --install-lib=%{_gamesdatadir}/%{name} \
    --skip-build
popd

# __main__.py is the game launcher
install -d %{buildroot}%{_gamesbindir}
ln -s %{_gamesdatadir}/%{name}/__main__.py %{buildroot}%{_gamesbindir}/%{name}
chmod +x %{buildroot}%{_gamesdatadir}/%{name}/__main__.py

# Install dist files
pushd %{_builddir}/%{name}-%{version}/res/share
install -D -m644 applications/%{name}.desktop \
    %{buildroot}%{_datadir}/applications/%{name}.desktop
install -D -m644 glib-2.0/schemas/com.joansala.%{name}.gschema.xml \
    %{buildroot}%{_datadir}/glib-2.0/schemas/com.joansala.%{name}.gschema.xml
install -D -m644 man/man6/%{name}.6 \
    %{buildroot}%{_mandir}/man6/%{name}.6
install -D -m644 mime/packages/%{name}.xml \
    %{buildroot}%{_datadir}/mime/packages/%{name}.xml
install -D -m644 icons/hicolor/scalable/mimetypes/text-x-oware-ogn.svg \
    %{buildroot}%{_iconsdir}/hicolor/scalable/mimetypes/text-x-oware-ogn.svg
install -D -m644 icons/hicolor/scalable/apps/%{name}.svg \
    %{buildroot}%{_iconsdir}/hicolor/scalable/apps/%{name}.svg
popd

# Move installed locales
pushd %{buildroot}%{_gamesdatadir}/%{name}/res
mv -v messages %{buildroot}%{_datadir}/locale
popd

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc AUTHORS COPYING NEWS README
%dir %{_datadir}/glib-2.0
%dir %{_datadir}/glib-2.0/schemas
%dir %{_iconsdir}/hicolor
%dir %{_iconsdir}/hicolor/scalable
%dir %{_iconsdir}/hicolor/scalable/apps
%dir %{_iconsdir}/hicolor/scalable/mimetypes
%{_gamesbindir}/%{name}
%{_gamesdatadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/glib-2.0/schemas/com.joansala.%{name}.gschema.xml
%{_datadir}/mime/packages/%{name}.xml
%{_iconsdir}/hicolor/scalable/apps/%{name}.svg
%{_iconsdir}/hicolor/scalable/mimetypes/text-x-oware-ogn.svg
%{_mandir}/man6/%{name}.6*

%post
%{_bindir}/glib-compile-schemas %{_datadir}/glib-2.0/schemas || :
%{_bindir}/gtk-update-icon-cache %{_iconsdir} &> /dev/null || :
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
%{_bindir}/update-desktop-database &> /dev/null || :

%postun
%{_bindir}/glib-compile-schemas %{_datadir}/glib-2.0/schemas || :
%{_bindir}/gtk-update-icon-cache %{_iconsdir}/hicolor/ &> /dev/null || :
%{_bindir}/update-mime-database %{_datadir}/mime &> /dev/null || :
%{_bindir}/update-desktop-database &> /dev/null || :

%changelog
* Fri Nov 13 2015 Joan Sala <contact@joansala.com>
- 1.1.0-2
- Fix OpenSUSE dependencies

* Sun Nov 8 2015 Joan Sala <contact@joansala.com>
- 1.1.0-1
- auale 1.1.0 release

