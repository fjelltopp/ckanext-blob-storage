import { render, act, fireEvent, screen } from '@testing-library/react';
import App from './src/app';
import axios from 'axios'
import * as giftless from "giftless-client";

jest.mock('axios');
giftless.Client = jest.fn(() => ({
  default: jest.fn(),
  upload: jest.fn()
}));

//afterEach(() => screen.debug())

async function renderAppComponent(existingResourceData) {
  await act(async () => {

    // arrange
    const mockedAppProps = {
      lfsServer: 'mockedLfsServer',
      orgId: 'mockedOrgId',
      datasetId: 'mockedDatasetId',
      existingResourceData: existingResourceData
    };
    const mockedAxiosPost = axios.post.mockImplementation(() =>
      Promise.resolve({
        data: { result: { token: 'MockedToken' } }
      })
    );

    // act
    const { getByTestId } = render(<App {...mockedAppProps} />);

    // wait for intial useEffect to run
    await new Promise(resolve => setTimeout(resolve, 20));
    expect(mockedAxiosPost).toHaveBeenCalled();

    // assert
    if (existingResourceData.urlType === null) {
      expect(getByTestId('FileUploaderButton')).toBeInTheDocument();
      expect(getByTestId('UrlUploaderButton')).toBeInTheDocument();
    }

  })
}

describe('upload a new resources', () => {

  beforeEach(async () => {
    await renderAppComponent({
      urlType: null,
      url: null,
      sha256: null,
      fileName: null,
      size: null,
    });
  })

  describe('url upload', () => {

    test('correct inputs are displayed', async () => {

      // act
      fireEvent.click(screen.getByTestId('UrlUploaderButton'));
      expect(screen.getByTestId('UrlUploaderComponent')).toBeInTheDocument();
      expect(screen.getByTestId('UrlInputField')).toBeInTheDocument();

      // assert
      expect(screen.getByTestId('url_type')).toHaveValue('')
      expect(screen.getByTestId('lfs_prefix')).toHaveValue('')
      expect(screen.getByTestId('sha256')).toHaveValue('')
      expect(screen.getByTestId('size')).toHaveValue('')

    });

  });

  describe('file upload', () => {

    const uploadFileToElement = async elementTestId => {
      // arrange
      const component = screen.getByTestId(elementTestId);

      // act
      const file = new File(['file'], 'data.json');
      Object.defineProperty(component, 'files', { value: [file] });
      fireEvent.drop(component);

      // assert
      await screen.findByText('data.json')
    }

    test('file upload using the <input type="file" />', async () => {
      await uploadFileToElement('FileUploaderInput');
    });

    test('file upload using drag and drop', async () => {
      await uploadFileToElement('FileUploaderComponent');
    });

    test('correct inputs are displayed', async () => {

      // arrange & act
      await uploadFileToElement('FileUploaderInput');

      // assert
      expect(screen.getByTestId('url_type')).toHaveValue('upload')
      expect(screen.getByTestId('lfs_prefix')).toHaveValue('mockedOrgId/mockedDatasetId')
      expect(screen.getByTestId('sha256')).toHaveValue('mockedSha256')
      expect(screen.getByTestId('size')).toHaveValue('1337')
    });

  });
});

describe('view an existing resources', () => {

  describe('url upload', () => {

    test('correct inputs are displayed', async () => {

      // arrange
      const existingResourceData = {
        urlType: '', // empty string means it's a url upload
        url: 'existingUrl',
      };

      // act
      await renderAppComponent(existingResourceData);

      // assert
      expect(screen.getByTestId('UrlInputField')).toHaveValue(existingResourceData.url)
      expect(screen.getByTestId('url_type')).toHaveValue(existingResourceData.urlType)
      // no need to assert anything else as ckan backend will
      // ignore all the other fields like sha256, size etc

    });

  });

  describe('file upload', () => {

    test('correct inputs are displayed', async () => {

      // arrange
      const existingResourceData = {
        urlType: 'upload', // 'upload' means it's a file upload
        url: 'existingUrl',
        sha256: 'existingSha256',
        fileName: 'existingFileName',
        size: 'existingSize',
      };

      // act
      await renderAppComponent(existingResourceData);

      // assert
      expect(screen.getByTestId('url_type')).toHaveValue(existingResourceData.urlType)
      expect(screen.getByTestId('lfs_prefix')).toHaveValue('mockedOrgId/mockedDatasetId')
      expect(screen.getByTestId('sha256')).toHaveValue(existingResourceData.sha256)
      expect(screen.getByTestId('size')).toHaveValue(existingResourceData.size)

    });

  });

});